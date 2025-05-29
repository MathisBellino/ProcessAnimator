"""
Keyframe data processor for robot animations.

This module handles the processing, validation, and manipulation of keyframe data
for robot animations, including rotation interpolation and bone data extraction.
"""

import numpy as np
import json
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KeyframeProcessor:
    """
    Processes and validates keyframe data for robot animations.
    
    This class provides functionality to:
    - Validate keyframe data structure
    - Extract bone rotation data
    - Interpolate between keyframes using various methods
    - Convert between different rotation representations
    """
    
    def __init__(self):
        """Initialize the keyframe processor."""
        self.supported_interpolations = ["BEZIER", "LINEAR", "CONSTANT"]
        self.required_keyframe_fields = ["bone", "frame", "rotation", "interpolation"]
        
    def validate_keyframe_data(self, keyframe_data: Dict[str, Any]) -> bool:
        """
        Validate the structure and content of keyframe data.
        
        Args:
            keyframe_data: Dictionary containing keyframe information
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check required top-level fields
            if not isinstance(keyframe_data, dict):
                logger.error("Keyframe data must be a dictionary")
                return False
                
            required_fields = ["armature", "keyframes"]
            for field in required_fields:
                if field not in keyframe_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate armature name
            if not isinstance(keyframe_data["armature"], str):
                logger.error("Armature name must be a string")
                return False
            
            # Validate keyframes
            keyframes = keyframe_data["keyframes"]
            if not isinstance(keyframes, list) or len(keyframes) == 0:
                logger.error("Keyframes must be a non-empty list")
                return False
            
            for i, keyframe in enumerate(keyframes):
                if not self._validate_single_keyframe(keyframe):
                    logger.error(f"Invalid keyframe at index {i}")
                    return False
            
            # Validate constraints if present
            if "constraints" in keyframe_data:
                if not self._validate_constraints(keyframe_data["constraints"]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating keyframe data: {e}")
            return False
    
    def _validate_single_keyframe(self, keyframe: Dict[str, Any]) -> bool:
        """Validate a single keyframe entry."""
        for field in self.required_keyframe_fields:
            if field not in keyframe:
                logger.error(f"Missing required keyframe field: {field}")
                return False
        
        # Validate frame number
        if not isinstance(keyframe["frame"], (int, float)) or keyframe["frame"] < 0:
            logger.error("Frame must be a non-negative number")
            return False
        
        # Validate rotation
        rotation = keyframe["rotation"]
        if not isinstance(rotation, (list, tuple)) or len(rotation) != 3:
            logger.error("Rotation must be a 3-element tuple/list")
            return False
        
        if not all(isinstance(r, (int, float)) for r in rotation):
            logger.error("All rotation values must be numbers")
            return False
        
        # Validate interpolation type
        if keyframe["interpolation"] not in self.supported_interpolations:
            logger.error(f"Unsupported interpolation: {keyframe['interpolation']}")
            return False
        
        return True
    
    def _validate_constraints(self, constraints: List[Dict[str, Any]]) -> bool:
        """Validate constraint data."""
        if not isinstance(constraints, list):
            logger.error("Constraints must be a list")
            return False
        
        for constraint in constraints:
            required_fields = ["bone", "type"]
            for field in required_fields:
                if field not in constraint:
                    logger.error(f"Missing required constraint field: {field}")
                    return False
        
        return True
    
    def extract_bone_rotations(self, keyframe_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract rotation data organized by bone name.
        
        Args:
            keyframe_data: Validated keyframe data
            
        Returns:
            Dictionary mapping bone names to lists of rotation keyframes
        """
        bone_rotations = {}
        
        for keyframe in keyframe_data["keyframes"]:
            bone_name = keyframe["bone"]
            
            if bone_name not in bone_rotations:
                bone_rotations[bone_name] = []
            
            bone_rotations[bone_name].append({
                "frame": keyframe["frame"],
                "rotation": keyframe["rotation"],
                "interpolation": keyframe["interpolation"]
            })
        
        # Sort keyframes by frame number for each bone
        for bone_name in bone_rotations:
            bone_rotations[bone_name].sort(key=lambda x: x["frame"])
        
        return bone_rotations
    
    def interpolate_rotation(self, start_rotation: Tuple[float, float, float], 
                           end_rotation: Tuple[float, float, float], 
                           t: float, 
                           method: str = "LINEAR") -> Tuple[float, float, float]:
        """
        Interpolate between two rotations.
        
        Args:
            start_rotation: Starting rotation (x, y, z) in radians
            end_rotation: Ending rotation (x, y, z) in radians
            t: Interpolation parameter (0.0 to 1.0)
            method: Interpolation method ("LINEAR", "BEZIER", "CONSTANT")
            
        Returns:
            Interpolated rotation tuple
        """
        if method == "CONSTANT":
            return start_rotation if t < 1.0 else end_rotation
        
        elif method == "LINEAR":
            return self._linear_interpolation(start_rotation, end_rotation, t)
        
        elif method == "BEZIER":
            # For simplicity, using cubic bezier with automatic control points
            return self._bezier_interpolation(start_rotation, end_rotation, t)
        
        else:
            logger.warning(f"Unknown interpolation method: {method}, using LINEAR")
            return self._linear_interpolation(start_rotation, end_rotation, t)
    
    def _linear_interpolation(self, start: Tuple[float, float, float], 
                            end: Tuple[float, float, float], 
                            t: float) -> Tuple[float, float, float]:
        """Perform linear interpolation between two rotations."""
        return tuple(start[i] + t * (end[i] - start[i]) for i in range(3))
    
    def _bezier_interpolation(self, start: Tuple[float, float, float], 
                            end: Tuple[float, float, float], 
                            t: float) -> Tuple[float, float, float]:
        """Perform cubic Bezier interpolation between two rotations."""
        # Generate control points automatically (1/3 and 2/3 of the way)
        control1 = tuple(start[i] + 0.33 * (end[i] - start[i]) for i in range(3))
        control2 = tuple(start[i] + 0.67 * (end[i] - start[i]) for i in range(3))
        
        # Cubic Bezier formula: (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        result = []
        for i in range(3):
            value = (
                (1 - t)**3 * start[i] +
                3 * (1 - t)**2 * t * control1[i] +
                3 * (1 - t) * t**2 * control2[i] +
                t**3 * end[i]
            )
            result.append(value)
        
        return tuple(result)
    
    def generate_interpolated_frames(self, bone_rotations: Dict[str, List[Dict[str, Any]]], 
                                   total_frames: int) -> Dict[str, List[Tuple[float, float, float]]]:
        """
        Generate interpolated rotation values for all frames.
        
        Args:
            bone_rotations: Bone rotation data from extract_bone_rotations
            total_frames: Total number of frames to generate
            
        Returns:
            Dictionary mapping bone names to lists of rotation tuples for each frame
        """
        interpolated_data = {}
        
        for bone_name, keyframes in bone_rotations.items():
            interpolated_data[bone_name] = []
            
            for frame in range(1, total_frames + 1):
                rotation = self._get_rotation_at_frame(keyframes, frame)
                interpolated_data[bone_name].append(rotation)
        
        return interpolated_data
    
    def _get_rotation_at_frame(self, keyframes: List[Dict[str, Any]], 
                              target_frame: int) -> Tuple[float, float, float]:
        """Get the rotation value at a specific frame, interpolating if necessary."""
        # Find the keyframes that bracket the target frame
        before_keyframe = None
        after_keyframe = None
        
        for keyframe in keyframes:
            if keyframe["frame"] <= target_frame:
                before_keyframe = keyframe
            elif keyframe["frame"] > target_frame and after_keyframe is None:
                after_keyframe = keyframe
                break
        
        # If we have an exact match
        if before_keyframe and before_keyframe["frame"] == target_frame:
            return tuple(before_keyframe["rotation"])
        
        # If we only have a before keyframe (hold the last value)
        if before_keyframe and not after_keyframe:
            return tuple(before_keyframe["rotation"])
        
        # If we only have an after keyframe (use the first value)
        if not before_keyframe and after_keyframe:
            return tuple(after_keyframe["rotation"])
        
        # Interpolate between keyframes
        if before_keyframe and after_keyframe:
            frame_diff = after_keyframe["frame"] - before_keyframe["frame"]
            t = (target_frame - before_keyframe["frame"]) / frame_diff
            
            return self.interpolate_rotation(
                tuple(before_keyframe["rotation"]),
                tuple(after_keyframe["rotation"]),
                t,
                before_keyframe["interpolation"]
            )
        
        # Fallback to zero rotation
        return (0.0, 0.0, 0.0)
    
    def export_to_blender_format(self, keyframe_data: Dict[str, Any]) -> str:
        """
        Export keyframe data to Blender-compatible Python script.
        
        Args:
            keyframe_data: Validated keyframe data
            
        Returns:
            Python script string for Blender execution
        """
        script_lines = [
            "import bpy",
            "import mathutils",
            "",
            "# Clear existing keyframes",
            "bpy.context.scene.frame_set(1)",
            "if bpy.context.object and bpy.context.object.type == 'ARMATURE':",
            "    bpy.ops.object.mode_set(mode='POSE')",
            "    bpy.ops.pose.select_all(action='SELECT')",
            "    bpy.ops.anim.keyframe_clear_v3d()",
            "",
            "# Set keyframes"
        ]
        
        for keyframe in keyframe_data["keyframes"]:
            bone_name = keyframe["bone"]
            frame = keyframe["frame"]
            rotation = keyframe["rotation"]
            
            script_lines.extend([
                f"bpy.context.scene.frame_set({frame})",
                f"bone = bpy.context.object.pose.bones['{bone_name}']",
                f"bone.rotation_euler = {rotation}",
                f"bone.keyframe_insert(data_path='rotation_euler')",
            ])
        
        return "\n".join(script_lines) 