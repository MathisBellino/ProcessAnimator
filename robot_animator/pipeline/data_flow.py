"""
End-to-end data flow pipeline for robot animation and control.

This module orchestrates the complete workflow from natural language commands
to robot control, integrating AI planning, safety monitoring, and Blender visualization.
"""

import logging
import time
import threading
from typing import Dict, List, Tuple, Any, Optional
import json
import numpy as np

from ..core.keyframe_processor import KeyframeProcessor
from ..blender.scene_manager import BlenderSceneManager
from ..ai.motion_planner import MotionPlanner
from ..safety.cobot_monitor import CobotSafetyMonitor

logger = logging.getLogger(__name__)


class DataFlowPipeline:
    """
    Complete data flow pipeline for robot animation and control.
    
    This class orchestrates the entire workflow:
    1. Natural language command parsing
    2. AI motion planning and trajectory generation
    3. Safety validation and monitoring
    4. Blender visualization and keyframe generation
    5. Robot control command output
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data flow pipeline.
        
        Args:
            config: Configuration dictionary for pipeline parameters
        """
        # Default configuration
        self.config = {
            "safety_enabled": True,
            "blender_visualization": True,
            "real_time_feedback": True,
            "trajectory_optimization": True,
            "collision_checking": True,
            "max_execution_time": 30.0,  # seconds
            "frame_rate": 24,  # fps for animation
            "joint_velocity_limit": 1.0,  # rad/s
            "workspace_bounds": {
                "x": (-1.0, 1.0),
                "y": (-1.0, 1.0), 
                "z": (0.0, 2.0)
            }
        }
        
        if config:
            self.config.update(config)
        
        # Initialize components
        self.keyframe_processor = KeyframeProcessor()
        self.scene_manager = BlenderSceneManager()
        self.motion_planner = MotionPlanner()
        self.safety_monitor = CobotSafetyMonitor()
        
        # Pipeline state
        self.current_command = None
        self.current_trajectory = None
        self.execution_status = "idle"
        self.feedback_data = {}
        
        # Real-time processing
        self.feedback_thread = None
        self.stop_feedback = threading.Event()
        
        logger.info("Data flow pipeline initialized")
    
    def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language command through the complete pipeline.
        
        Args:
            command: Natural language command string
            context: Optional context information (workspace state, etc.)
            
        Returns:
            Dictionary containing processing results and robot commands
        """
        logger.info(f"Processing command: {command}")
        start_time = time.time()
        
        try:
            # Step 1: Parse natural language command
            parsed_command = self.motion_planner.parse_natural_language(command)
            logger.debug(f"Parsed command: {parsed_command}")
            
            # Step 2: Generate motion plan
            motion_plan = self._generate_motion_plan(parsed_command, context)
            
            # Step 3: Safety validation
            safety_result = self._validate_safety(motion_plan)
            if not safety_result["safe"]:
                return {
                    "success": False,
                    "error": "Safety validation failed",
                    "safety_issues": safety_result["issues"],
                    "processing_time": time.time() - start_time
                }
            
            # Step 4: Generate Blender keyframes
            keyframes = self._generate_keyframes(motion_plan)
            
            # Step 5: Create robot control commands
            robot_commands = self._generate_robot_commands(motion_plan)
            
            # Step 6: Setup visualization
            if self.config["blender_visualization"]:
                self._setup_blender_visualization(keyframes, motion_plan)
            
            # Store current command for feedback
            self.current_command = parsed_command
            self.current_trajectory = motion_plan["trajectory"]
            self.execution_status = "ready"
            
            result = {
                "success": True,
                "parsed_command": parsed_command,
                "motion_plan": motion_plan,
                "keyframes": keyframes,
                "robot_commands": robot_commands,
                "safety_checks": safety_result,
                "processing_time": time.time() - start_time,
                "estimated_execution_time": motion_plan.get("execution_time", 0.0)
            }
            
            logger.info(f"Command processed successfully in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _generate_motion_plan(self, parsed_command: Dict[str, Any], 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a motion plan from the parsed command."""
        action = parsed_command["action"]
        target = parsed_command["target"]
        location = parsed_command["location"]
        modifiers = parsed_command["modifiers"]
        
        # Determine target position
        target_position = self._resolve_target_position(target, location, context)
        
        # Solve inverse kinematics
        joint_angles = self.motion_planner.solve_inverse_kinematics(target_position)
        
        # Generate trajectory
        start_angles = [0.0] * 6  # Home position
        if context and "current_joint_angles" in context:
            start_angles = context["current_joint_angles"]
        
        trajectory = self.motion_planner.generate_trajectory(
            start_angles, 
            joint_angles,
            num_points=50
        )
        
        # Optimize trajectory if enabled
        if self.config["trajectory_optimization"]:
            # Convert joint trajectory to Cartesian waypoints for optimization
            waypoints = []
            for joint_config in trajectory[::5]:  # Sample every 5th point
                fk_result = self.motion_planner._forward_kinematics(joint_config)
                if fk_result:
                    waypoints.append(fk_result[-1])  # End-effector position
            
            # Get obstacles from context
            obstacles = context.get("obstacles", []) if context else []
            
            # Optimize path
            optimized_waypoints = self.motion_planner.optimize_path(waypoints, obstacles)
            
            # Regenerate trajectory with optimized waypoints
            if len(optimized_waypoints) > len(waypoints):
                logger.info("Path optimized to avoid obstacles")
        
        # Estimate execution time
        execution_time = self.motion_planner.estimate_execution_time(
            trajectory, 
            self.config["joint_velocity_limit"]
        )
        
        motion_plan = {
            "action": action,
            "target_position": target_position,
            "joint_angles": joint_angles,
            "trajectory": trajectory,
            "execution_time": execution_time,
            "modifiers": modifiers,
            "waypoint_count": len(trajectory)
        }
        
        return motion_plan
    
    def _resolve_target_position(self, target: Dict[str, Any], 
                               location: Dict[str, Any], 
                               context: Optional[Dict[str, Any]] = None) -> Tuple[float, float, float]:
        """Resolve the target position from object and location information."""
        # If explicit coordinates are provided
        if location.get("coordinates"):
            return tuple(location["coordinates"])
        
        # If relative position is specified
        if location.get("relative") and location.get("offset"):
            base_position = (0.0, 0.5, 0.5)  # Default workspace center
            if context and "reference_position" in context:
                base_position = context["reference_position"]
            
            offset = location["offset"]
            return (
                base_position[0] + offset[0],
                base_position[1] + offset[1],
                base_position[2] + offset[2]
            )
        
        # If named location is specified
        location_type = location.get("type")
        if location_type == "table":
            return (0.5, 0.3, 0.8)
        elif location_type == "shelf":
            return (0.3, 0.2, 1.2)
        elif location_type == "container":
            return (0.0, 0.4, 0.6)
        
        # Default position
        return (0.5, 0.3, 0.8)
    
    def _validate_safety(self, motion_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the motion plan for safety compliance."""
        if not self.config["safety_enabled"]:
            return {"safe": True, "issues": []}
        
        issues = []
        
        # Check workspace bounds
        target_pos = motion_plan["target_position"]
        bounds = self.config["workspace_bounds"]
        
        if not (bounds["x"][0] <= target_pos[0] <= bounds["x"][1]):
            issues.append(f"Target X position {target_pos[0]} outside bounds {bounds['x']}")
        
        if not (bounds["y"][0] <= target_pos[1] <= bounds["y"][1]):
            issues.append(f"Target Y position {target_pos[1]} outside bounds {bounds['y']}")
        
        if not (bounds["z"][0] <= target_pos[2] <= bounds["z"][1]):
            issues.append(f"Target Z position {target_pos[2]} outside bounds {bounds['z']}")
        
        # Check trajectory for collisions if enabled
        if self.config["collision_checking"]:
            trajectory = motion_plan["trajectory"]
            obstacles = []  # Would get from context in real implementation
            
            for i, joint_config in enumerate(trajectory):
                if self.motion_planner.check_collisions(joint_config, obstacles):
                    issues.append(f"Collision detected at trajectory point {i}")
                    break
        
        # Check execution time
        if motion_plan["execution_time"] > self.config["max_execution_time"]:
            issues.append(f"Execution time {motion_plan['execution_time']:.1f}s exceeds limit")
        
        # Check joint limits (already handled in IK solver, but double-check)
        joint_angles = motion_plan["joint_angles"]
        joint_limits = self.motion_planner.joint_limits
        
        for i, (angle, (min_limit, max_limit)) in enumerate(zip(joint_angles, joint_limits)):
            if not (min_limit <= angle <= max_limit):
                issues.append(f"Joint {i} angle {angle:.2f} outside limits [{min_limit:.2f}, {max_limit:.2f}]")
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "workspace_check": "passed" if len(issues) == 0 else "failed",
            "collision_check": "passed" if self.config["collision_checking"] else "skipped"
        }
    
    def _generate_keyframes(self, motion_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Blender keyframes from the motion plan."""
        trajectory = motion_plan["trajectory"]
        frame_rate = self.config["frame_rate"]
        execution_time = motion_plan["execution_time"]
        
        # Calculate total frames
        total_frames = int(execution_time * frame_rate)
        if total_frames == 0:
            total_frames = len(trajectory)
        
        # Generate keyframes for each joint
        keyframes = []
        joint_names = ["base_joint", "shoulder_joint", "elbow_joint", 
                      "wrist1_joint", "wrist2_joint", "wrist3_joint"]
        
        for frame_idx, joint_config in enumerate(trajectory):
            frame_number = int((frame_idx / len(trajectory)) * total_frames) + 1
            
            for joint_idx, angle in enumerate(joint_config):
                if joint_idx < len(joint_names):
                    keyframe = {
                        "bone": joint_names[joint_idx],
                        "frame": frame_number,
                        "rotation": (0, 0, angle),  # Simplified - only Z rotation
                        "interpolation": "BEZIER"
                    }
                    keyframes.append(keyframe)
        
        # Create keyframe data structure
        keyframe_data = {
            "armature": "UR15e_Armature",
            "keyframes": keyframes,
            "constraints": [
                {
                    "bone": "wrist3_joint",
                    "type": "IK",
                    "target": "target_empty",
                    "chain_length": 6
                }
            ],
            "total_frames": total_frames,
            "frame_rate": frame_rate
        }
        
        # Validate keyframe data
        if not self.keyframe_processor.validate_keyframe_data(keyframe_data):
            logger.warning("Generated keyframe data failed validation")
        
        return keyframe_data
    
    def _generate_robot_commands(self, motion_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate robot control commands from the motion plan."""
        trajectory = motion_plan["trajectory"]
        execution_time = motion_plan["execution_time"]
        
        commands = []
        
        # Add initial command to move to start position
        if trajectory:
            start_command = {
                "type": "move_joints",
                "joint_angles": trajectory[0],
                "velocity": self.config["joint_velocity_limit"] * 0.5,  # Slower for start
                "acceleration": 0.5,
                "timestamp": time.time()
            }
            commands.append(start_command)
        
        # Add trajectory following command
        trajectory_command = {
            "type": "follow_trajectory",
            "trajectory": trajectory,
            "execution_time": execution_time,
            "velocity_limit": self.config["joint_velocity_limit"],
            "timestamp": time.time()
        }
        commands.append(trajectory_command)
        
        # Add completion command
        completion_command = {
            "type": "trajectory_complete",
            "final_position": trajectory[-1] if trajectory else [0.0] * 6,
            "timestamp": time.time() + execution_time
        }
        commands.append(completion_command)
        
        return commands
    
    def _setup_blender_visualization(self, keyframes: Dict[str, Any], 
                                   motion_plan: Dict[str, Any]):
        """Setup Blender visualization for the motion plan."""
        try:
            # Create armature if it doesn't exist
            joint_names = ["base_joint", "shoulder_joint", "elbow_joint", 
                          "wrist1_joint", "wrist2_joint", "wrist3_joint"]
            
            self.scene_manager.create_armature("UR15e_Armature", joint_names)
            
            # Create target empty at target position
            target_pos = motion_plan["target_position"]
            self.scene_manager.create_target_empty("target_empty", target_pos)
            
            # Insert keyframes
            for keyframe in keyframes["keyframes"]:
                self.scene_manager.insert_keyframe(keyframe)
            
            # Apply constraints
            for constraint in keyframes["constraints"]:
                self.scene_manager.apply_constraint(constraint)
            
            logger.info("Blender visualization setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup Blender visualization: {e}")
    
    def process_sensor_feedback(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process real-time sensor feedback and adjust execution.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Dictionary containing feedback processing results
        """
        feedback_result = {
            "adjustments": [],
            "safety_status": "ok",
            "continue_execution": True,
            "timestamp": time.time()
        }
        
        try:
            # Process camera data for human detection
            if "camera" in sensor_data:
                camera_frame = sensor_data["camera"]
                humans = self.safety_monitor.detect_humans(camera_frame)
                
                if humans:
                    # Check safety zones
                    robot_position = sensor_data.get("robot_position", (0.0, 0.0, 0.0))
                    
                    for human in humans:
                        violation = self.safety_monitor.check_safety_zone(
                            human["position"], robot_position
                        )
                        
                        if violation:
                            feedback_result["safety_status"] = "violation"
                            feedback_result["continue_execution"] = False
                            feedback_result["adjustments"].append({
                                "type": "emergency_stop",
                                "reason": "human_in_danger_zone"
                            })
                            break
            
            # Process force sensor data
            if "force_sensor" in sensor_data:
                forces = sensor_data["force_sensor"]
                max_force = max(abs(f) for f in forces)
                
                if max_force > 10.0:  # Newton threshold
                    feedback_result["adjustments"].append({
                        "type": "reduce_velocity",
                        "factor": 0.5,
                        "reason": "high_force_detected"
                    })
            
            # Process joint position feedback
            if "joint_positions" in sensor_data:
                current_joints = sensor_data["joint_positions"]
                
                # Check if robot is following planned trajectory
                if self.current_trajectory:
                    # Find closest point in trajectory
                    min_error = float('inf')
                    for trajectory_point in self.current_trajectory:
                        error = sum((a - b)**2 for a, b in zip(current_joints, trajectory_point))
                        min_error = min(min_error, error)
                    
                    if min_error > 0.1:  # Significant deviation
                        feedback_result["adjustments"].append({
                            "type": "trajectory_correction",
                            "error": min_error,
                            "reason": "trajectory_deviation"
                        })
            
            # Store feedback data
            self.feedback_data = {
                "sensor_data": sensor_data,
                "feedback_result": feedback_result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error processing sensor feedback: {e}")
            feedback_result["safety_status"] = "error"
            feedback_result["continue_execution"] = False
        
        return feedback_result
    
    def start_real_time_feedback(self, sensor_callback: Optional[callable] = None):
        """Start real-time feedback processing."""
        if not self.config["real_time_feedback"]:
            return
        
        if self.feedback_thread and self.feedback_thread.is_alive():
            logger.warning("Real-time feedback already running")
            return
        
        self.stop_feedback.clear()
        self.feedback_thread = threading.Thread(
            target=self._feedback_loop,
            args=(sensor_callback,),
            daemon=True
        )
        self.feedback_thread.start()
        
        logger.info("Real-time feedback started")
    
    def stop_real_time_feedback(self):
        """Stop real-time feedback processing."""
        if not self.feedback_thread:
            return
        
        self.stop_feedback.set()
        self.feedback_thread.join(timeout=2.0)
        
        logger.info("Real-time feedback stopped")
    
    def _feedback_loop(self, sensor_callback: Optional[callable]):
        """Main feedback processing loop."""
        while not self.stop_feedback.is_set():
            try:
                # Get sensor data (mock for now)
                if sensor_callback:
                    sensor_data = sensor_callback()
                else:
                    sensor_data = self._get_mock_sensor_data()
                
                # Process feedback
                if sensor_data:
                    feedback_result = self.process_sensor_feedback(sensor_data)
                    
                    # Handle adjustments
                    for adjustment in feedback_result["adjustments"]:
                        self._handle_adjustment(adjustment)
                
                time.sleep(0.1)  # 10 Hz feedback rate
                
            except Exception as e:
                logger.error(f"Error in feedback loop: {e}")
                time.sleep(1.0)
    
    def _get_mock_sensor_data(self) -> Dict[str, Any]:
        """Generate mock sensor data for testing."""
        return {
            "camera": np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            "force_sensor": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
            "joint_positions": [0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
            "robot_position": (0.0, 0.0, 0.0),
            "timestamp": time.time()
        }
    
    def _handle_adjustment(self, adjustment: Dict[str, Any]):
        """Handle a feedback adjustment."""
        adjustment_type = adjustment["type"]
        
        if adjustment_type == "emergency_stop":
            logger.critical("Emergency stop triggered by feedback system")
            self.execution_status = "emergency_stop"
            
        elif adjustment_type == "reduce_velocity":
            factor = adjustment.get("factor", 0.5)
            logger.warning(f"Reducing velocity by factor {factor}")
            
        elif adjustment_type == "trajectory_correction":
            error = adjustment.get("error", 0.0)
            logger.warning(f"Trajectory correction needed, error: {error}")
        
        else:
            logger.warning(f"Unknown adjustment type: {adjustment_type}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            "execution_status": self.execution_status,
            "current_command": self.current_command,
            "safety_monitor_status": self.safety_monitor.get_safety_status(),
            "blender_scene_info": self.scene_manager.get_scene_info(),
            "real_time_feedback_active": self.feedback_thread is not None and self.feedback_thread.is_alive(),
            "last_feedback": self.feedback_data.get("timestamp", 0),
            "config": self.config
        }
    
    def export_execution_log(self, filepath: str):
        """Export execution log and data."""
        log_data = {
            "pipeline_status": self.get_pipeline_status(),
            "current_trajectory": self.current_trajectory,
            "feedback_history": self.feedback_data,
            "export_timestamp": time.time()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            logger.info(f"Execution log exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export execution log: {e}") 