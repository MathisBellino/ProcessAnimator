"""
Collaborative robot safety monitoring system.

This module provides real-time safety monitoring for human-robot collaboration,
including computer vision-based human detection, safety zone monitoring,
and emergency stop functionality.
"""

import numpy as np
import logging
import time
import threading
from typing import Dict, List, Tuple, Any, Optional, Callable
import json
import math

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - using mock computer vision")


class CobotSafetyMonitor:
    """
    Safety monitoring system for collaborative robots.
    
    This class provides functionality to:
    - Detect humans in the workspace using computer vision
    - Monitor safety zones around the robot
    - Trigger emergency stops when necessary
    - Track human poses and predict intentions
    """
    
    def __init__(self, safety_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the safety monitor.
        
        Args:
            safety_config: Configuration dictionary for safety parameters
        """
        self.emergency_stop_active = False
        self.monitoring_active = False
        self.safety_violations = []
        
        # Default safety configuration
        self.config = {
            "safety_zones": {
                "danger_zone": 0.5,    # meters - immediate stop
                "warning_zone": 1.0,   # meters - slow down
                "monitoring_zone": 2.0  # meters - track humans
            },
            "max_human_velocity": 2.0,  # m/s - for prediction
            "emergency_stop_delay": 0.1,  # seconds
            "pose_detection_confidence": 0.5,
            "tracking_history_length": 30  # frames
        }
        
        if safety_config:
            self.config.update(safety_config)
        
        # Human tracking data
        self.detected_humans = []
        self.human_tracking_history = {}
        self.pose_estimator = None
        
        # Callbacks for safety events
        self.emergency_stop_callback = None
        self.warning_callback = None
        
        # Monitoring thread
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        if CV2_AVAILABLE:
            self._setup_computer_vision()
    
    def _setup_computer_vision(self):
        """Setup computer vision components for human detection."""
        try:
            # Load pre-trained human detection model (YOLO or similar)
            # For this implementation, we'll use a simplified approach
            self.human_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            )
            
            # Setup background subtractor for motion detection
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )
            
            logger.info("Computer vision components initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup computer vision: {e}")
            self.human_cascade = None
            self.bg_subtractor = None
    
    def detect_humans(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect humans in a camera frame.
        
        Args:
            frame: Camera frame as numpy array (H, W, 3)
            
        Returns:
            List of detected human dictionaries with position and confidence
        """
        humans = []
        
        if not CV2_AVAILABLE or frame is None:
            # Mock detection for testing
            if hasattr(self, '_mock_human_count'):
                for i in range(self._mock_human_count):
                    humans.append({
                        "id": i,
                        "position": (0.5 + i * 0.3, 0.5, 0.0),
                        "confidence": 0.8,
                        "bbox": (100 + i * 50, 100, 50, 150),
                        "velocity": (0.0, 0.0, 0.0)
                    })
            return humans
        
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect humans using cascade classifier
            if self.human_cascade:
                detections = self.human_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                for i, (x, y, w, h) in enumerate(detections):
                    # Convert pixel coordinates to world coordinates
                    world_pos = self._pixel_to_world(x + w//2, y + h, frame.shape)
                    
                    human = {
                        "id": i,
                        "position": world_pos,
                        "confidence": 0.7,  # Simplified confidence
                        "bbox": (x, y, w, h),
                        "velocity": self._estimate_velocity(i, world_pos)
                    }
                    
                    humans.append(human)
            
            # Update tracking history
            self._update_tracking_history(humans)
            
            # Store detected humans
            self.detected_humans = humans
            
            logger.debug(f"Detected {len(humans)} humans in frame")
            
        except Exception as e:
            logger.error(f"Error in human detection: {e}")
        
        return humans
    
    def _pixel_to_world(self, pixel_x: int, pixel_y: int, frame_shape: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """
        Convert pixel coordinates to world coordinates.
        
        This is a simplified conversion - in practice, you'd use camera calibration.
        """
        height, width = frame_shape[:2]
        
        # Assume camera is positioned above the workspace
        # Simple perspective transformation
        world_x = (pixel_x - width // 2) / width * 2.0  # -1 to 1 meters
        world_y = (height - pixel_y) / height * 2.0     # 0 to 2 meters depth
        world_z = 0.0  # Assume humans are on the ground
        
        return (world_x, world_y, world_z)
    
    def _estimate_velocity(self, human_id: int, current_position: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Estimate human velocity based on position history."""
        if human_id not in self.human_tracking_history:
            return (0.0, 0.0, 0.0)
        
        history = self.human_tracking_history[human_id]
        if len(history) < 2:
            return (0.0, 0.0, 0.0)
        
        # Calculate velocity from last two positions
        prev_pos, prev_time = history[-1]
        current_time = time.time()
        
        dt = current_time - prev_time
        if dt > 0:
            velocity = (
                (current_position[0] - prev_pos[0]) / dt,
                (current_position[1] - prev_pos[1]) / dt,
                (current_position[2] - prev_pos[2]) / dt
            )
        else:
            velocity = (0.0, 0.0, 0.0)
        
        return velocity
    
    def _update_tracking_history(self, humans: List[Dict[str, Any]]):
        """Update the tracking history for detected humans."""
        current_time = time.time()
        max_history = self.config["tracking_history_length"]
        
        for human in humans:
            human_id = human["id"]
            position = human["position"]
            
            if human_id not in self.human_tracking_history:
                self.human_tracking_history[human_id] = []
            
            # Add current position to history
            self.human_tracking_history[human_id].append((position, current_time))
            
            # Limit history length
            if len(self.human_tracking_history[human_id]) > max_history:
                self.human_tracking_history[human_id].pop(0)
    
    def check_safety_zone(self, human_position: Tuple[float, float, float], 
                         robot_position: Tuple[float, float, float]) -> bool:
        """
        Check if a human is violating safety zones around the robot.
        
        Args:
            human_position: Human position (x, y, z)
            robot_position: Robot position (x, y, z)
            
        Returns:
            True if safety violation detected, False otherwise
        """
        # Calculate distance between human and robot
        distance = math.sqrt(
            (human_position[0] - robot_position[0])**2 +
            (human_position[1] - robot_position[1])**2 +
            (human_position[2] - robot_position[2])**2
        )
        
        zones = self.config["safety_zones"]
        
        # Check danger zone (immediate stop)
        if distance < zones["danger_zone"]:
            violation = {
                "type": "danger_zone",
                "distance": distance,
                "human_position": human_position,
                "robot_position": robot_position,
                "timestamp": time.time(),
                "severity": "critical"
            }
            self.safety_violations.append(violation)
            
            logger.critical(f"DANGER ZONE VIOLATION: Human at {distance:.2f}m from robot")
            self.trigger_emergency_stop()
            return True
        
        # Check warning zone (slow down)
        elif distance < zones["warning_zone"]:
            violation = {
                "type": "warning_zone",
                "distance": distance,
                "human_position": human_position,
                "robot_position": robot_position,
                "timestamp": time.time(),
                "severity": "warning"
            }
            self.safety_violations.append(violation)
            
            logger.warning(f"WARNING ZONE: Human at {distance:.2f}m from robot")
            if self.warning_callback:
                self.warning_callback(violation)
            return True
        
        return False
    
    def predict_human_trajectory(self, human_data: Dict[str, Any], 
                               prediction_time: float = 2.0) -> List[Tuple[float, float, float]]:
        """
        Predict future human positions based on current velocity.
        
        Args:
            human_data: Human detection data with position and velocity
            prediction_time: Time horizon for prediction in seconds
            
        Returns:
            List of predicted positions
        """
        current_pos = human_data["position"]
        velocity = human_data["velocity"]
        
        # Simple linear prediction (could be enhanced with ML models)
        predicted_positions = []
        
        num_steps = int(prediction_time * 10)  # 10 Hz prediction
        dt = prediction_time / num_steps
        
        for i in range(num_steps):
            t = i * dt
            predicted_pos = (
                current_pos[0] + velocity[0] * t,
                current_pos[1] + velocity[1] * t,
                current_pos[2] + velocity[2] * t
            )
            predicted_positions.append(predicted_pos)
        
        return predicted_positions
    
    def assess_collision_risk(self, human_data: Dict[str, Any], 
                            robot_trajectory: List[Tuple[float, float, float]]) -> float:
        """
        Assess the risk of collision between human and robot trajectories.
        
        Args:
            human_data: Human detection data
            robot_trajectory: Planned robot trajectory
            
        Returns:
            Risk score from 0.0 (no risk) to 1.0 (high risk)
        """
        if not robot_trajectory:
            return 0.0
        
        # Predict human trajectory
        human_trajectory = self.predict_human_trajectory(human_data)
        
        min_distance = float('inf')
        collision_time = None
        
        # Check for potential intersections
        for i, robot_pos in enumerate(robot_trajectory):
            if i < len(human_trajectory):
                human_pos = human_trajectory[i]
                
                distance = math.sqrt(
                    (robot_pos[0] - human_pos[0])**2 +
                    (robot_pos[1] - human_pos[1])**2 +
                    (robot_pos[2] - human_pos[2])**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    collision_time = i * 0.1  # 10 Hz
        
        # Calculate risk score based on minimum distance and time
        danger_threshold = self.config["safety_zones"]["danger_zone"]
        
        if min_distance < danger_threshold:
            # High risk if trajectories intersect within danger zone
            risk_score = 1.0 - (min_distance / danger_threshold)
            
            # Increase risk if collision is imminent
            if collision_time and collision_time < 1.0:
                risk_score = min(1.0, risk_score * (2.0 - collision_time))
        else:
            risk_score = 0.0
        
        logger.debug(f"Collision risk assessment: {risk_score:.2f}")
        return risk_score
    
    def trigger_emergency_stop(self):
        """Trigger an emergency stop of the robot."""
        if not self.emergency_stop_active:
            self.emergency_stop_active = True
            
            logger.critical("EMERGENCY STOP TRIGGERED")
            
            # Call emergency stop callback if registered
            if self.emergency_stop_callback:
                self.emergency_stop_callback()
            
            # Log the emergency stop event
            emergency_event = {
                "type": "emergency_stop",
                "timestamp": time.time(),
                "reason": "safety_violation",
                "detected_humans": len(self.detected_humans),
                "violations": self.safety_violations[-5:]  # Last 5 violations
            }
            
            logger.critical(f"Emergency stop event: {emergency_event}")
    
    def reset_emergency_stop(self):
        """Reset the emergency stop state."""
        self.emergency_stop_active = False
        logger.info("Emergency stop reset")
    
    def start_monitoring(self, camera_source: int = 0):
        """
        Start continuous safety monitoring.
        
        Args:
            camera_source: Camera device index or video file path
        """
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.stop_monitoring.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(camera_source,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Safety monitoring started")
    
    def stop_monitoring_system(self):
        """Stop the safety monitoring system."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        self.stop_monitoring.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        logger.info("Safety monitoring stopped")
    
    def _monitoring_loop(self, camera_source: int):
        """Main monitoring loop running in separate thread."""
        if not CV2_AVAILABLE:
            logger.warning("Camera monitoring not available - using mock mode")
            return
        
        try:
            cap = cv2.VideoCapture(camera_source)
            
            while not self.stop_monitoring.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read camera frame")
                    break
                
                # Detect humans in frame
                humans = self.detect_humans(frame)
                
                # Check safety zones for each detected human
                robot_position = (0.0, 0.0, 0.0)  # Would get from robot controller
                
                for human in humans:
                    self.check_safety_zone(human["position"], robot_position)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        finally:
            self.monitoring_active = False
    
    def register_emergency_callback(self, callback: Callable[[], None]):
        """Register a callback function for emergency stop events."""
        self.emergency_stop_callback = callback
        logger.info("Emergency stop callback registered")
    
    def register_warning_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback function for warning events."""
        self.warning_callback = callback
        logger.info("Warning callback registered")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get current safety system status.
        
        Returns:
            Dictionary containing safety status information
        """
        return {
            "emergency_stop_active": self.emergency_stop_active,
            "monitoring_active": self.monitoring_active,
            "detected_humans": len(self.detected_humans),
            "recent_violations": len([v for v in self.safety_violations 
                                    if time.time() - v["timestamp"] < 60]),
            "safety_zones": self.config["safety_zones"],
            "last_detection_time": max([h.get("timestamp", 0) for h in self.detected_humans], default=0)
        }
    
    def export_safety_log(self, filepath: str):
        """
        Export safety violations and events to a log file.
        
        Args:
            filepath: Path to save the safety log
        """
        safety_data = {
            "config": self.config,
            "violations": self.safety_violations,
            "export_timestamp": time.time(),
            "total_violations": len(self.safety_violations)
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(safety_data, f, indent=2)
            
            logger.info(f"Safety log exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export safety log: {e}")
    
    # Mock methods for testing
    def _set_mock_human_count(self, count: int):
        """Set number of mock humans for testing."""
        self._mock_human_count = count 