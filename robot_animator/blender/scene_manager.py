"""
Blender scene management for robot animation.

This module provides integration with Blender's Python API for creating
and manipulating 3D scenes, armatures, and animation constraints.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)

try:
    import bpy
    import mathutils
    BLENDER_AVAILABLE = True
except ImportError:
    # Mock bpy for testing environments
    BLENDER_AVAILABLE = False
    logger.warning("Blender not available - using mock implementation")


class BlenderSceneManager:
    """
    Manages Blender scenes for robot animation visualization.
    
    This class provides functionality to:
    - Create and manage robot armatures
    - Insert keyframes into the timeline
    - Apply constraints (IK, tracking, etc.)
    - Export animations and scenes
    """
    
    def __init__(self):
        """Initialize the Blender scene manager."""
        self.constraint_applied = False
        self.current_armature = None
        self.scene_objects = {}
        
        if BLENDER_AVAILABLE:
            self.context = bpy.context
            self.data = bpy.data
            self.ops = bpy.ops
        else:
            # Mock objects for testing
            self._setup_mock_blender()
    
    def _setup_mock_blender(self):
        """Setup mock Blender objects for testing."""
        class MockOps:
            class object:
                @staticmethod
                def armature_add():
                    pass
                
                @staticmethod
                def mode_set(mode='OBJECT'):
                    pass
            
            class anim:
                @staticmethod
                def keyframe_insert():
                    pass
                
                @staticmethod
                def keyframe_clear_v3d():
                    pass
            
            class pose:
                @staticmethod
                def select_all(action='SELECT'):
                    pass
        
        class MockContext:
            def __init__(self):
                self.object = None
                self.scene = MockScene()
        
        class MockScene:
            def __init__(self):
                self.frame_current = 1
            
            def frame_set(self, frame):
                self.frame_current = frame
        
        self.ops = MockOps()
        self.context = MockContext()
        self.data = {}
    
    def create_armature(self, armature_name: str, joint_names: Optional[List[str]] = None) -> bool:
        """
        Create a robot armature in the Blender scene.
        
        Args:
            armature_name: Name for the armature object
            joint_names: List of joint/bone names to create
            
        Returns:
            bool: True if armature was created successfully
        """
        try:
            if BLENDER_AVAILABLE:
                # Clear existing selection
                bpy.ops.object.select_all(action='DESELECT')
                
                # Add armature
                bpy.ops.object.armature_add(enter_editmode=True)
                armature_obj = bpy.context.active_object
                armature_obj.name = armature_name
                
                # Get the armature data
                armature_data = armature_obj.data
                armature_data.name = f"{armature_name}_Data"
                
                if joint_names:
                    self._create_bone_hierarchy(armature_data, joint_names)
                
                # Switch back to object mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
                self.current_armature = armature_obj
                self.scene_objects[armature_name] = armature_obj
                
            else:
                # Mock implementation
                self.ops.object.armature_add()
                self.current_armature = armature_name
                self.scene_objects[armature_name] = armature_name
            
            logger.info(f"Created armature: {armature_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create armature {armature_name}: {e}")
            return False
    
    def _create_bone_hierarchy(self, armature_data, joint_names: List[str]):
        """Create a hierarchy of bones for the robot joints."""
        if not BLENDER_AVAILABLE:
            return
        
        # Remove default bone
        if armature_data.edit_bones:
            armature_data.edit_bones.remove(armature_data.edit_bones[0])
        
        # Create bones for each joint
        previous_bone = None
        for i, joint_name in enumerate(joint_names):
            bone = armature_data.edit_bones.new(joint_name)
            
            # Position bones in a chain
            if previous_bone:
                bone.head = previous_bone.tail
                bone.parent = previous_bone
            else:
                bone.head = (0, 0, 0)
            
            # Set tail position (length of bone)
            bone.tail = (bone.head[0], bone.head[1], bone.head[2] + 0.2)
            
            previous_bone = bone
    
    def insert_keyframe(self, keyframe_data: Dict[str, Any]) -> bool:
        """
        Insert a keyframe into the Blender timeline.
        
        Args:
            keyframe_data: Dictionary containing keyframe information
            
        Returns:
            bool: True if keyframe was inserted successfully
        """
        try:
            bone_name = keyframe_data["bone"]
            frame = keyframe_data["frame"]
            rotation = keyframe_data["rotation"]
            
            if BLENDER_AVAILABLE:
                # Set current frame
                bpy.context.scene.frame_set(frame)
                
                # Get the armature and switch to pose mode
                if self.current_armature:
                    bpy.context.view_layer.objects.active = self.current_armature
                    bpy.ops.object.mode_set(mode='POSE')
                    
                    # Get the pose bone
                    pose_bone = self.current_armature.pose.bones.get(bone_name)
                    if pose_bone:
                        # Set rotation
                        pose_bone.rotation_euler = rotation
                        
                        # Insert keyframe
                        pose_bone.keyframe_insert(data_path="rotation_euler")
                        
                        logger.debug(f"Inserted keyframe for {bone_name} at frame {frame}")
                    else:
                        logger.warning(f"Bone {bone_name} not found in armature")
                        return False
            else:
                # Mock implementation
                self.context.scene.frame_set(frame)
                self.ops.anim.keyframe_insert()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert keyframe: {e}")
            return False
    
    def apply_constraint(self, constraint_data: Dict[str, Any]) -> bool:
        """
        Apply a constraint to a bone.
        
        Args:
            constraint_data: Dictionary containing constraint information
            
        Returns:
            bool: True if constraint was applied successfully
        """
        try:
            bone_name = constraint_data["bone"]
            constraint_type = constraint_data["type"]
            
            if BLENDER_AVAILABLE:
                if self.current_armature:
                    bpy.context.view_layer.objects.active = self.current_armature
                    bpy.ops.object.mode_set(mode='POSE')
                    
                    pose_bone = self.current_armature.pose.bones.get(bone_name)
                    if pose_bone:
                        if constraint_type == "IK":
                            self._apply_ik_constraint(pose_bone, constraint_data)
                        elif constraint_type == "TRACK_TO":
                            self._apply_track_constraint(pose_bone, constraint_data)
                        else:
                            logger.warning(f"Unknown constraint type: {constraint_type}")
                            return False
                    else:
                        logger.warning(f"Bone {bone_name} not found")
                        return False
            
            self.constraint_applied = True
            logger.info(f"Applied {constraint_type} constraint to {bone_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply constraint: {e}")
            return False
    
    def _apply_ik_constraint(self, pose_bone, constraint_data: Dict[str, Any]):
        """Apply an IK constraint to a pose bone."""
        if not BLENDER_AVAILABLE:
            return
        
        # Create IK constraint
        ik_constraint = pose_bone.constraints.new(type='IK')
        ik_constraint.name = f"IK_{pose_bone.name}"
        
        # Set target if specified
        if "target" in constraint_data:
            target_name = constraint_data["target"]
            target_obj = bpy.data.objects.get(target_name)
            if target_obj:
                ik_constraint.target = target_obj
        
        # Set chain length if specified
        if "chain_length" in constraint_data:
            ik_constraint.chain_count = constraint_data["chain_length"]
        
        # Set other IK properties
        ik_constraint.use_tail = True
        ik_constraint.use_stretch = False
    
    def _apply_track_constraint(self, pose_bone, constraint_data: Dict[str, Any]):
        """Apply a track-to constraint to a pose bone."""
        if not BLENDER_AVAILABLE:
            return
        
        # Create track-to constraint
        track_constraint = pose_bone.constraints.new(type='TRACK_TO')
        track_constraint.name = f"Track_{pose_bone.name}"
        
        # Set target if specified
        if "target" in constraint_data:
            target_name = constraint_data["target"]
            target_obj = bpy.data.objects.get(target_name)
            if target_obj:
                track_constraint.target = target_obj
        
        # Set tracking axis
        track_constraint.track_axis = 'TRACK_Y'
        track_constraint.up_axis = 'UP_Z'
    
    def create_target_empty(self, name: str, location: Tuple[float, float, float]) -> bool:
        """
        Create an empty object to serve as a target for constraints.
        
        Args:
            name: Name for the empty object
            location: 3D location for the empty
            
        Returns:
            bool: True if empty was created successfully
        """
        try:
            if BLENDER_AVAILABLE:
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
                empty_obj = bpy.context.active_object
                empty_obj.name = name
                
                self.scene_objects[name] = empty_obj
                logger.info(f"Created target empty: {name} at {location}")
            else:
                # Mock implementation
                self.scene_objects[name] = {"location": location}
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create target empty {name}: {e}")
            return False
    
    def animate_to_target(self, target_name: str, target_position: Tuple[float, float, float], 
                         duration_frames: int = 50) -> bool:
        """
        Animate a target object to a new position.
        
        Args:
            target_name: Name of the target object
            target_position: New position for the target
            duration_frames: Number of frames for the animation
            
        Returns:
            bool: True if animation was created successfully
        """
        try:
            if BLENDER_AVAILABLE:
                target_obj = bpy.data.objects.get(target_name)
                if not target_obj:
                    logger.warning(f"Target object {target_name} not found")
                    return False
                
                # Set keyframe at current frame
                current_frame = bpy.context.scene.frame_current
                target_obj.keyframe_insert(data_path="location")
                
                # Move to end frame and set new position
                bpy.context.scene.frame_set(current_frame + duration_frames)
                target_obj.location = target_position
                target_obj.keyframe_insert(data_path="location")
                
                # Return to original frame
                bpy.context.scene.frame_set(current_frame)
                
                logger.info(f"Animated {target_name} to {target_position}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to animate target {target_name}: {e}")
            return False
    
    def export_animation(self, filepath: str, format: str = "FBX") -> bool:
        """
        Export the current animation to a file.
        
        Args:
            filepath: Path to save the animation file
            format: Export format ("FBX", "GLTF", "BLEND")
            
        Returns:
            bool: True if export was successful
        """
        try:
            if not BLENDER_AVAILABLE:
                logger.info(f"Mock export to {filepath} in {format} format")
                return True
            
            if format.upper() == "FBX":
                bpy.ops.export_scene.fbx(filepath=filepath)
            elif format.upper() == "GLTF":
                bpy.ops.export_scene.gltf(filepath=filepath)
            elif format.upper() == "BLEND":
                bpy.ops.wm.save_as_mainfile(filepath=filepath)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported animation to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export animation: {e}")
            return False
    
    def clear_scene(self) -> bool:
        """
        Clear all objects from the current scene.
        
        Returns:
            bool: True if scene was cleared successfully
        """
        try:
            if BLENDER_AVAILABLE:
                # Select all objects
                bpy.ops.object.select_all(action='SELECT')
                
                # Delete all selected objects
                bpy.ops.object.delete(use_global=False)
                
                # Clear orphaned data
                bpy.ops.outliner.orphans_purge()
            
            # Reset internal state
            self.current_armature = None
            self.scene_objects.clear()
            self.constraint_applied = False
            
            logger.info("Cleared Blender scene")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear scene: {e}")
            return False
    
    def get_scene_info(self) -> Dict[str, Any]:
        """
        Get information about the current scene.
        
        Returns:
            Dictionary containing scene information
        """
        # Handle current_armature being either a string or an object with .name
        armature_name = None
        if self.current_armature:
            if hasattr(self.current_armature, 'name'):
                armature_name = self.current_armature.name
            else:
                armature_name = str(self.current_armature)
        
        info = {
            "objects": list(self.scene_objects.keys()),
            "current_armature": armature_name,
            "constraints_applied": self.constraint_applied
        }
        
        if BLENDER_AVAILABLE:
            info.update({
                "current_frame": bpy.context.scene.frame_current,
                "frame_start": bpy.context.scene.frame_start,
                "frame_end": bpy.context.scene.frame_end,
                "total_objects": len(bpy.data.objects)
            })
        
        return info 