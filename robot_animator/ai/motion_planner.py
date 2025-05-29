"""
AI-powered motion planning for robot animation.

This module provides intelligent motion planning capabilities including
natural language processing, inverse kinematics solving, and collision detection.
"""

import numpy as np
import re
import logging
from typing import Dict, List, Tuple, Any, Optional
import json
import math

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available - using simplified NLP")


class MotionPlanner:
    """
    AI-powered motion planner for robot animations.
    
    This class provides functionality to:
    - Parse natural language commands into robot actions
    - Solve inverse kinematics for target positions
    - Detect collisions in the workspace
    - Generate optimized motion paths
    """
    
    def __init__(self):
        """Initialize the motion planner."""
        self.action_keywords = {
            "pick_up": ["pick", "grab", "take", "lift", "grasp"],
            "place": ["place", "put", "drop", "set", "position"],
            "move": ["move", "go", "navigate", "travel"],
            "rotate": ["rotate", "turn", "spin", "twist"],
            "stop": ["stop", "halt", "pause", "freeze"]
        }
        
        self.object_keywords = {
            "cube": ["cube", "box", "block"],
            "sphere": ["sphere", "ball", "orb"],
            "cylinder": ["cylinder", "tube", "pipe"],
            "tool": ["tool", "wrench", "screwdriver", "hammer"]
        }
        
        self.color_keywords = ["red", "blue", "green", "yellow", "black", "white", "orange", "purple"]
        
        # Robot configuration (UR15e-like)
        self.joint_limits = [
            (-2*math.pi, 2*math.pi),  # Base joint
            (-math.pi, math.pi),      # Shoulder joint
            (-math.pi, math.pi),      # Elbow joint
            (-2*math.pi, 2*math.pi),  # Wrist 1
            (-2*math.pi, 2*math.pi),  # Wrist 2
            (-2*math.pi, 2*math.pi)   # Wrist 3
        ]
        
        self.link_lengths = [0.1625, 0.425, 0.3922, 0.1333, 0.0997, 0.0996]  # UR15e dimensions
        
        if TRANSFORMERS_AVAILABLE:
            self._setup_nlp_pipeline()
    
    def _setup_nlp_pipeline(self):
        """Setup the natural language processing pipeline."""
        try:
            # Use a lightweight model for intent classification
            self.nlp_pipeline = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            logger.info("NLP pipeline initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize NLP pipeline: {e}")
            self.nlp_pipeline = None
    
    def parse_natural_language(self, command: str) -> Dict[str, Any]:
        """
        Parse a natural language command into structured robot actions.
        
        Args:
            command: Natural language command string
            
        Returns:
            Dictionary containing parsed action information
        """
        command_lower = command.lower()
        
        # Extract action
        action = self._extract_action(command_lower)
        
        # Extract target object
        target_object = self._extract_object(command_lower)
        
        # Extract location/direction
        location = self._extract_location(command_lower)
        
        # Extract modifiers (speed, precision, etc.)
        modifiers = self._extract_modifiers(command_lower)
        
        parsed_command = {
            "action": action,
            "target": target_object,
            "location": location,
            "modifiers": modifiers,
            "original_command": command
        }
        
        logger.info(f"Parsed command: {parsed_command}")
        return parsed_command
    
    def _extract_action(self, command: str) -> str:
        """Extract the primary action from the command."""
        for action, keywords in self.action_keywords.items():
            for keyword in keywords:
                if keyword in command:
                    return action
        
        # Default action if none found
        return "move"
    
    def _extract_object(self, command: str) -> Dict[str, Any]:
        """Extract target object information from the command."""
        object_info = {"type": None, "color": None, "descriptor": None}
        
        # Find object type
        for obj_type, keywords in self.object_keywords.items():
            for keyword in keywords:
                if keyword in command:
                    object_info["type"] = obj_type
                    break
        
        # Find color
        for color in self.color_keywords:
            if color in command:
                object_info["color"] = color
                break
        
        # Extract descriptive words
        descriptors = re.findall(r'\b(small|large|big|tiny|heavy|light)\b', command)
        if descriptors:
            object_info["descriptor"] = descriptors[0]
        
        return object_info
    
    def _extract_location(self, command: str) -> Dict[str, Any]:
        """Extract location/direction information from the command."""
        location_info = {"type": None, "coordinates": None, "relative": None}
        
        # Look for specific coordinates
        coord_pattern = r'(\d+\.?\d*),?\s*(\d+\.?\d*),?\s*(\d+\.?\d*)'
        coords = re.search(coord_pattern, command)
        if coords:
            location_info["coordinates"] = [float(coords.group(i)) for i in range(1, 4)]
        
        # Look for relative positions
        relative_terms = {
            "above": (0, 0, 0.1),
            "below": (0, 0, -0.1),
            "left": (-0.1, 0, 0),
            "right": (0.1, 0, 0),
            "forward": (0, 0.1, 0),
            "backward": (0, -0.1, 0)
        }
        
        for term, offset in relative_terms.items():
            if term in command:
                location_info["relative"] = term
                location_info["offset"] = offset
                break
        
        # Look for named locations
        if "table" in command:
            location_info["type"] = "table"
        elif "shelf" in command:
            location_info["type"] = "shelf"
        elif "bin" in command or "box" in command:
            location_info["type"] = "container"
        
        return location_info
    
    def _extract_modifiers(self, command: str) -> Dict[str, Any]:
        """Extract command modifiers (speed, precision, etc.)."""
        modifiers = {}
        
        # Speed modifiers
        if any(word in command for word in ["slow", "slowly", "careful"]):
            modifiers["speed"] = "slow"
        elif any(word in command for word in ["fast", "quick", "rapid"]):
            modifiers["speed"] = "fast"
        else:
            modifiers["speed"] = "normal"
        
        # Precision modifiers
        if any(word in command for word in ["precise", "accurate", "exact"]):
            modifiers["precision"] = "high"
        elif any(word in command for word in ["rough", "approximate"]):
            modifiers["precision"] = "low"
        else:
            modifiers["precision"] = "normal"
        
        return modifiers
    
    def solve_inverse_kinematics(self, target_position: Tuple[float, float, float], 
                                target_orientation: Optional[Tuple[float, float, float]] = None) -> List[float]:
        """
        Solve inverse kinematics for a target end-effector position.
        
        Args:
            target_position: Target (x, y, z) position
            target_orientation: Optional target orientation (rx, ry, rz)
            
        Returns:
            List of joint angles in radians
        """
        x, y, z = target_position
        
        # Simplified IK solver for 6-DOF robot arm
        # This is a basic geometric approach - in practice, you'd use more sophisticated methods
        
        # Calculate base rotation
        theta1 = math.atan2(y, x)
        
        # Calculate wrist position (subtract wrist length from target)
        wrist_x = x - self.link_lengths[5] * math.cos(theta1)
        wrist_y = y - self.link_lengths[5] * math.sin(theta1)
        wrist_z = z - self.link_lengths[0]  # Subtract base height
        
        # Distance from shoulder to wrist
        r = math.sqrt(wrist_x**2 + wrist_y**2)
        s = wrist_z
        
        # Distance in shoulder plane
        d = math.sqrt(r**2 + s**2)
        
        # Check if target is reachable
        max_reach = self.link_lengths[1] + self.link_lengths[2]
        if d > max_reach:
            logger.warning(f"Target position {target_position} is out of reach")
            # Scale down to maximum reach
            scale = max_reach / d * 0.95  # 95% of max reach for safety
            wrist_x *= scale
            wrist_y *= scale
            wrist_z *= scale
            r = math.sqrt(wrist_x**2 + wrist_y**2)
            s = wrist_z
            d = math.sqrt(r**2 + s**2)
        
        # Calculate elbow angle using law of cosines
        cos_theta3 = (d**2 - self.link_lengths[1]**2 - self.link_lengths[2]**2) / (2 * self.link_lengths[1] * self.link_lengths[2])
        cos_theta3 = max(-1, min(1, cos_theta3))  # Clamp to valid range
        theta3 = math.acos(cos_theta3)
        
        # Calculate shoulder angle
        alpha = math.atan2(s, r)
        beta = math.acos((self.link_lengths[1]**2 + d**2 - self.link_lengths[2]**2) / (2 * self.link_lengths[1] * d))
        theta2 = alpha - beta
        
        # Wrist angles (simplified - assume pointing down)
        if target_orientation:
            theta4, theta5, theta6 = target_orientation
        else:
            theta4 = 0
            theta5 = -(theta2 + theta3)  # Keep end-effector pointing down
            theta6 = 0
        
        joint_angles = [theta1, theta2, theta3, theta4, theta5, theta6]
        
        # Apply joint limits
        for i, (angle, (min_limit, max_limit)) in enumerate(zip(joint_angles, self.joint_limits)):
            joint_angles[i] = max(min_limit, min(max_limit, angle))
        
        logger.debug(f"IK solution for {target_position}: {joint_angles}")
        return joint_angles
    
    def check_collisions(self, joint_angles: List[float], obstacles: List[Dict[str, Any]]) -> bool:
        """
        Check for collisions between robot and obstacles.
        
        Args:
            joint_angles: Current joint configuration
            obstacles: List of obstacle dictionaries with position and radius
            
        Returns:
            True if collision detected, False otherwise
        """
        # Calculate forward kinematics to get link positions
        link_positions = self._forward_kinematics(joint_angles)
        
        # Check each link against each obstacle
        for i, link_pos in enumerate(link_positions):
            for obstacle in obstacles:
                obs_pos = obstacle["position"]
                obs_radius = obstacle.get("radius", 0.1)
                
                # Calculate distance between link and obstacle
                distance = math.sqrt(
                    (link_pos[0] - obs_pos[0])**2 +
                    (link_pos[1] - obs_pos[1])**2 +
                    (link_pos[2] - obs_pos[2])**2
                )
                
                # Assume link has some radius (simplified collision model)
                link_radius = 0.05
                
                if distance < (obs_radius + link_radius):
                    logger.warning(f"Collision detected between link {i} and obstacle at {obs_pos}")
                    return True
        
        return False
    
    def _forward_kinematics(self, joint_angles: List[float]) -> List[Tuple[float, float, float]]:
        """
        Calculate forward kinematics to get link positions.
        
        Args:
            joint_angles: Joint angles in radians
            
        Returns:
            List of (x, y, z) positions for each link
        """
        positions = []
        
        # Base position
        x, y, z = 0, 0, self.link_lengths[0]
        positions.append((x, y, z))
        
        # Calculate cumulative transformations
        theta1, theta2, theta3, theta4, theta5, theta6 = joint_angles
        
        # Shoulder position (after base rotation)
        x = 0
        y = 0
        z = self.link_lengths[0]
        positions.append((x, y, z))
        
        # Elbow position
        x = self.link_lengths[1] * math.cos(theta1) * math.cos(theta2)
        y = self.link_lengths[1] * math.sin(theta1) * math.cos(theta2)
        z = self.link_lengths[0] + self.link_lengths[1] * math.sin(theta2)
        positions.append((x, y, z))
        
        # Wrist position
        x += self.link_lengths[2] * math.cos(theta1) * math.cos(theta2 + theta3)
        y += self.link_lengths[2] * math.sin(theta1) * math.cos(theta2 + theta3)
        z += self.link_lengths[2] * math.sin(theta2 + theta3)
        positions.append((x, y, z))
        
        # End-effector position (simplified)
        x += self.link_lengths[5] * math.cos(theta1)
        y += self.link_lengths[5] * math.sin(theta1)
        positions.append((x, y, z))
        
        return positions
    
    def generate_trajectory(self, start_angles: List[float], end_angles: List[float], 
                          num_points: int = 50) -> List[List[float]]:
        """
        Generate a smooth trajectory between two joint configurations.
        
        Args:
            start_angles: Starting joint configuration
            end_angles: Ending joint configuration
            num_points: Number of interpolation points
            
        Returns:
            List of joint configurations forming the trajectory
        """
        trajectory = []
        
        for i in range(num_points):
            t = i / (num_points - 1)  # Parameter from 0 to 1
            
            # Use cubic interpolation for smooth motion
            t_smooth = 3*t**2 - 2*t**3  # Smooth step function
            
            current_angles = []
            for start_angle, end_angle in zip(start_angles, end_angles):
                angle = start_angle + t_smooth * (end_angle - start_angle)
                current_angles.append(angle)
            
            trajectory.append(current_angles)
        
        return trajectory
    
    def optimize_path(self, waypoints: List[Tuple[float, float, float]], 
                     obstacles: List[Dict[str, Any]]) -> List[Tuple[float, float, float]]:
        """
        Optimize a path to avoid obstacles and minimize travel time.
        
        Args:
            waypoints: List of (x, y, z) waypoints
            obstacles: List of obstacles to avoid
            
        Returns:
            Optimized list of waypoints
        """
        if len(waypoints) < 2:
            return waypoints
        
        optimized_path = [waypoints[0]]  # Start with first waypoint
        
        for i in range(1, len(waypoints)):
            current_point = optimized_path[-1]
            target_point = waypoints[i]
            
            # Check if direct path is collision-free
            if self._is_path_clear(current_point, target_point, obstacles):
                optimized_path.append(target_point)
            else:
                # Find intermediate waypoint to avoid obstacles
                intermediate = self._find_safe_intermediate(current_point, target_point, obstacles)
                if intermediate:
                    optimized_path.append(intermediate)
                optimized_path.append(target_point)
        
        logger.info(f"Optimized path from {len(waypoints)} to {len(optimized_path)} waypoints")
        return optimized_path
    
    def _is_path_clear(self, start: Tuple[float, float, float], 
                      end: Tuple[float, float, float], 
                      obstacles: List[Dict[str, Any]]) -> bool:
        """Check if a straight-line path is clear of obstacles."""
        num_checks = 20
        
        for i in range(num_checks):
            t = i / (num_checks - 1)
            point = (
                start[0] + t * (end[0] - start[0]),
                start[1] + t * (end[1] - start[1]),
                start[2] + t * (end[2] - start[2])
            )
            
            for obstacle in obstacles:
                obs_pos = obstacle["position"]
                obs_radius = obstacle.get("radius", 0.1)
                
                distance = math.sqrt(
                    (point[0] - obs_pos[0])**2 +
                    (point[1] - obs_pos[1])**2 +
                    (point[2] - obs_pos[2])**2
                )
                
                if distance < obs_radius + 0.05:  # Safety margin
                    return False
        
        return True
    
    def _find_safe_intermediate(self, start: Tuple[float, float, float], 
                               end: Tuple[float, float, float], 
                               obstacles: List[Dict[str, Any]]) -> Optional[Tuple[float, float, float]]:
        """Find a safe intermediate waypoint to avoid obstacles."""
        # Simple approach: try going around obstacles
        for obstacle in obstacles:
            obs_pos = obstacle["position"]
            obs_radius = obstacle.get("radius", 0.1)
            
            # Try going above the obstacle
            intermediate = (
                (start[0] + end[0]) / 2,
                (start[1] + end[1]) / 2,
                max(start[2], end[2], obs_pos[2] + obs_radius + 0.1)
            )
            
            if self._is_path_clear(start, intermediate, obstacles) and \
               self._is_path_clear(intermediate, end, obstacles):
                return intermediate
        
        return None
    
    def estimate_execution_time(self, trajectory: List[List[float]], 
                              max_joint_velocity: float = 1.0) -> float:
        """
        Estimate the execution time for a trajectory.
        
        Args:
            trajectory: List of joint configurations
            max_joint_velocity: Maximum joint velocity in rad/s
            
        Returns:
            Estimated execution time in seconds
        """
        if len(trajectory) < 2:
            return 0.0
        
        total_time = 0.0
        
        for i in range(1, len(trajectory)):
            prev_config = trajectory[i-1]
            curr_config = trajectory[i]
            
            # Calculate maximum joint displacement
            max_displacement = max(
                abs(curr_config[j] - prev_config[j]) 
                for j in range(len(curr_config))
            )
            
            # Time for this segment
            segment_time = max_displacement / max_joint_velocity
            total_time += segment_time
        
        return total_time 