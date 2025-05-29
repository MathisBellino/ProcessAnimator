#!/usr/bin/env python3
"""
Linkage Animator - Main animation generation system

Generates keyframe animations for multi-bar linkage mechanisms by:
- Calculating motion paths based on kinematic equations
- Creating smooth keyframe transitions
- Handling constraint-based animation
- Providing real-time animation controls
"""

import math
import logging
from typing import Dict, Any, List, Tuple, Optional

try:
    import bpy
    from mathutils import Vector, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

logger = logging.getLogger(__name__)


class LinkageAnimator:
    """
    Main animator for linkage mechanisms.
    
    Handles the complete animation pipeline from motion calculation
    to keyframe generation and Blender integration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize linkage animator.
        
        Args:
            config: Optional configuration for animation parameters
        """
        self.config = config or self._default_config()
        self.current_animation = None
        self.animation_cache = {}
        
        logger.info("Linkage animator initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for animation."""
        return {
            'frame_rate': 24,
            'default_duration': 5.0,  # seconds
            'interpolation_mode': 'BEZIER',
            'auto_keyframe': True,
            'smooth_motion': True,
            'motion_quality': 'medium',
            'constraint_solving': True,
            'real_time_update': True,
            'cache_calculations': True
        }
    
    def create_animation(self, animation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete animation for a linkage mechanism.
        
        Args:
            animation_request: Animation configuration and parameters
            
        Returns:
            Animation creation results
        """
        try:
            linkage_type = animation_request['linkage_type']
            parameters = animation_request['parameters']
            motion = animation_request['motion']
            
            logger.info(f"Creating {linkage_type} animation")
            
            # Get or create linkage mechanism
            if 'armature_object' in animation_request:
                armature_obj = animation_request['armature_object']
                if not BLENDER_AVAILABLE:
                    return self._simulate_animation_creation(animation_request)
            else:
                return {'success': False, 'error': 'No armature object provided'}
            
            # Calculate motion path
            motion_data = self._calculate_motion_path(linkage_type, parameters, motion)
            if not motion_data['success']:
                return motion_data
            
            # Generate keyframes
            keyframe_data = self._generate_keyframes(armature_obj, motion_data, motion)
            if not keyframe_data['success']:
                return keyframe_data
            
            # Apply keyframes to armature
            if BLENDER_AVAILABLE:
                apply_result = self._apply_keyframes_to_armature(armature_obj, keyframe_data)
            else:
                apply_result = {'success': True, 'note': 'Simulation mode'}
            
            # Setup animation timeline
            frame_count = keyframe_data['frame_count']
            if BLENDER_AVAILABLE:
                bpy.context.scene.frame_start = 1
                bpy.context.scene.frame_end = frame_count
                bpy.context.scene.frame_current = 1
            
            # Store animation data
            self.current_animation = {
                'linkage_type': linkage_type,
                'parameters': parameters,
                'motion': motion,
                'motion_data': motion_data,
                'keyframes': keyframe_data,
                'frame_count': frame_count
            }
            
            return {
                'success': True,
                'animation_data': self.current_animation,
                'frame_count': frame_count,
                'motion_path': motion_data['joint_paths'],
                'keyframe_count': len(keyframe_data['keyframes'])
            }
            
        except Exception as e:
            logger.error(f"Animation creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_motion_path(self, linkage_type: str, parameters: Dict[str, Any], 
                             motion: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate motion path for the linkage mechanism."""
        try:
            duration = motion.get('duration', self.config['default_duration'])
            frame_rate = self.config['frame_rate']
            total_frames = int(duration * frame_rate)
            
            if linkage_type == 'four_bar':
                return self._calculate_four_bar_motion(parameters, motion, total_frames)
            elif linkage_type == 'slider_crank':
                return self._calculate_slider_crank_motion(parameters, motion, total_frames)
            else:
                return {
                    'success': False,
                    'error': f'Motion calculation not implemented for {linkage_type}'
                }
                
        except Exception as e:
            logger.error(f"Motion calculation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_four_bar_motion(self, parameters: Dict[str, Any], 
                                 motion: Dict[str, Any], total_frames: int) -> Dict[str, Any]:
        """Calculate motion path for four-bar linkage."""
        from ..core.linkage_mechanisms import FourBarLinkage
        
        # Create linkage mechanism
        linkage = FourBarLinkage(
            parameters['ground_length'],
            parameters['input_length'],
            parameters['coupler_length'],
            parameters['output_length']
        )
        
        # Motion parameters
        rpm = motion.get('rpm', 60)
        motion_type = motion.get('type', 'constant_rotation')
        
        # Calculate angular velocity
        angular_velocity = (rpm * 2 * math.pi) / 60  # rad/s
        
        # Generate motion path
        joint_paths = {
            'ground_start': [],
            'input_joint': [],
            'coupler_joint': [],
            'ground_end': []
        }
        
        link_angles = {
            'input': [],
            'coupler': [],
            'output': []
        }
        
        for frame in range(total_frames):
            t = frame / self.config['frame_rate']  # Time in seconds
            
            if motion_type == 'constant_rotation':
                input_angle = angular_velocity * t
            else:
                input_angle = 0  # Fallback
            
            # Solve positions for this frame
            positions = linkage.solve_positions(input_angle)
            
            if positions['success']:
                joint_positions = positions['joint_positions']
                
                joint_paths['ground_start'].append(joint_positions[0])
                joint_paths['input_joint'].append(joint_positions[1])
                joint_paths['coupler_joint'].append(joint_positions[2])
                joint_paths['ground_end'].append(joint_positions[3])
                
                link_angles['input'].append(input_angle)
                link_angles['coupler'].append(positions['coupler_angle'])
                link_angles['output'].append(positions['output_angle'])
            else:
                # Use previous position if calculation fails
                if frame > 0:
                    for key in joint_paths:
                        joint_paths[key].append(joint_paths[key][-1])
                    for key in link_angles:
                        link_angles[key].append(link_angles[key][-1])
                else:
                    # Fallback to initial positions
                    for key in joint_paths:
                        joint_paths[key].append((0, 0, 0))
                    for key in link_angles:
                        link_angles[key].append(0)
        
        return {
            'success': True,
            'joint_paths': joint_paths,
            'link_angles': link_angles,
            'total_frames': total_frames,
            'linkage_mechanism': linkage
        }
    
    def _calculate_slider_crank_motion(self, parameters: Dict[str, Any],
                                     motion: Dict[str, Any], total_frames: int) -> Dict[str, Any]:
        """Calculate motion path for slider-crank mechanism."""
        from ..core.linkage_mechanisms import SliderCrankMechanism
        
        # Create linkage mechanism
        linkage = SliderCrankMechanism(
            parameters['crank_length'],
            parameters['connecting_rod_length']
        )
        
        # Motion parameters
        rpm = motion.get('rpm', 60)
        angular_velocity = (rpm * 2 * math.pi) / 60  # rad/s
        
        # Generate motion path
        joint_paths = {
            'crank_center': [],
            'crank_pin': [],
            'slider': []
        }
        
        motion_data = {
            'crank_angles': [],
            'slider_positions': [],
            'connecting_rod_angles': []
        }
        
        for frame in range(total_frames):
            t = frame / self.config['frame_rate']
            crank_angle = angular_velocity * t
            
            # Solve positions
            positions = linkage.solve_positions(crank_angle)
            
            if positions['success']:
                joint_positions = positions['joint_positions']
                
                joint_paths['crank_center'].append(joint_positions[0])
                joint_paths['crank_pin'].append(joint_positions[1])
                joint_paths['slider'].append(joint_positions[2])
                
                motion_data['crank_angles'].append(crank_angle)
                motion_data['slider_positions'].append(positions['slider_position'])
                motion_data['connecting_rod_angles'].append(positions['connecting_rod_angle'])
            else:
                # Use previous values if calculation fails
                if frame > 0:
                    for key in joint_paths:
                        joint_paths[key].append(joint_paths[key][-1])
                    for key in motion_data:
                        motion_data[key].append(motion_data[key][-1])
        
        return {
            'success': True,
            'joint_paths': joint_paths,
            'motion_data': motion_data,
            'total_frames': total_frames,
            'linkage_mechanism': linkage
        }
    
    def _generate_keyframes(self, armature_obj, motion_data: Dict[str, Any], 
                          motion: Dict[str, Any]) -> Dict[str, Any]:
        """Generate keyframes from motion data."""
        try:
            total_frames = motion_data['total_frames']
            keyframes = []
            
            if not BLENDER_AVAILABLE:
                return {
                    'success': True,
                    'keyframes': [],
                    'frame_count': total_frames,
                    'note': 'Simulation mode - no actual keyframes generated'
                }
            
            # Get bone names from armature
            bone_names = [bone.name for bone in armature_obj.data.bones]
            
            # Generate keyframes based on linkage type
            if 'link_angles' in motion_data:
                # Four-bar linkage keyframes
                keyframes = self._generate_four_bar_keyframes(
                    bone_names, motion_data, total_frames
                )
            elif 'motion_data' in motion_data:
                # Slider-crank keyframes
                keyframes = self._generate_slider_crank_keyframes(
                    bone_names, motion_data, total_frames
                )
            
            return {
                'success': True,
                'keyframes': keyframes,
                'frame_count': total_frames,
                'bone_count': len(bone_names)
            }
            
        except Exception as e:
            logger.error(f"Keyframe generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_four_bar_keyframes(self, bone_names: List[str], 
                                   motion_data: Dict[str, Any], total_frames: int) -> List[Dict[str, Any]]:
        """Generate keyframes for four-bar linkage."""
        keyframes = []
        link_angles = motion_data['link_angles']
        
        # Sample keyframes (not every frame for performance)
        sample_rate = max(1, total_frames // 60)  # ~60 keyframes max
        
        for frame_idx in range(0, total_frames, sample_rate):
            frame_number = frame_idx + 1
            
            # Input link rotation
            if 'input_link' in bone_names and frame_idx < len(link_angles['input']):
                input_angle = link_angles['input'][frame_idx]
                keyframes.append({
                    'bone': 'input_link',
                    'frame': frame_number,
                    'rotation': (0, 0, input_angle),
                    'type': 'rotation'
                })
            
            # Coupler link rotation
            if 'coupler_link' in bone_names and frame_idx < len(link_angles['coupler']):
                coupler_angle = link_angles['coupler'][frame_idx]
                keyframes.append({
                    'bone': 'coupler_link',
                    'frame': frame_number,
                    'rotation': (0, 0, coupler_angle),
                    'type': 'rotation'
                })
            
            # Output link rotation
            if 'output_link' in bone_names and frame_idx < len(link_angles['output']):
                output_angle = link_angles['output'][frame_idx]
                keyframes.append({
                    'bone': 'output_link',
                    'frame': frame_number,
                    'rotation': (0, 0, output_angle),
                    'type': 'rotation'
                })
        
        return keyframes
    
    def _generate_slider_crank_keyframes(self, bone_names: List[str],
                                       motion_data: Dict[str, Any], total_frames: int) -> List[Dict[str, Any]]:
        """Generate keyframes for slider-crank mechanism."""
        keyframes = []
        motion_values = motion_data['motion_data']
        joint_paths = motion_data['joint_paths']
        
        sample_rate = max(1, total_frames // 60)
        
        for frame_idx in range(0, total_frames, sample_rate):
            frame_number = frame_idx + 1
            
            # Crank rotation
            if 'crank' in bone_names and frame_idx < len(motion_values['crank_angles']):
                crank_angle = motion_values['crank_angles'][frame_idx]
                keyframes.append({
                    'bone': 'crank',
                    'frame': frame_number,
                    'rotation': (0, 0, crank_angle),
                    'type': 'rotation'
                })
            
            # Connecting rod rotation
            if 'connecting_rod' in bone_names and frame_idx < len(motion_values['connecting_rod_angles']):
                rod_angle = motion_values['connecting_rod_angles'][frame_idx]
                keyframes.append({
                    'bone': 'connecting_rod',
                    'frame': frame_number,
                    'rotation': (0, 0, rod_angle),
                    'type': 'rotation'
                })
            
            # Slider target position (if exists)
            if frame_idx < len(joint_paths['slider']):
                slider_pos = joint_paths['slider'][frame_idx]
                # This would update IK target position
                keyframes.append({
                    'target': 'slider_target',
                    'frame': frame_number,
                    'location': slider_pos,
                    'type': 'location'
                })
        
        return keyframes
    
    def _apply_keyframes_to_armature(self, armature_obj, keyframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply generated keyframes to the Blender armature."""
        if not BLENDER_AVAILABLE:
            return {'success': True, 'note': 'Simulation mode'}
        
        try:
            keyframes = keyframe_data['keyframes']
            
            # Set armature as active and switch to pose mode
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='POSE')
            
            # Clear existing animation data
            if armature_obj.animation_data:
                armature_obj.animation_data_clear()
            
            applied_keyframes = 0
            
            for keyframe in keyframes:
                frame_number = keyframe['frame']
                
                if keyframe['type'] == 'rotation' and 'bone' in keyframe:
                    bone_name = keyframe['bone']
                    rotation = keyframe['rotation']
                    
                    if bone_name in armature_obj.pose.bones:
                        pose_bone = armature_obj.pose.bones[bone_name]
                        
                        # Set frame
                        bpy.context.scene.frame_set(frame_number)
                        
                        # Set rotation
                        pose_bone.rotation_euler = Euler(rotation, 'XYZ')
                        
                        # Insert keyframe
                        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame_number)
                        applied_keyframes += 1
                
                elif keyframe['type'] == 'location' and 'target' in keyframe:
                    # Handle target object keyframes
                    target_name = keyframe['target']
                    location = keyframe['location']
                    
                    # Find target object
                    target_obj = bpy.data.objects.get(f"{armature_obj.name}_{target_name}")
                    if target_obj:
                        bpy.context.scene.frame_set(frame_number)
                        target_obj.location = Vector(location)
                        target_obj.keyframe_insert(data_path="location", frame=frame_number)
                        applied_keyframes += 1
            
            # Set interpolation mode
            if armature_obj.animation_data and armature_obj.animation_data.action:
                for fcurve in armature_obj.animation_data.action.fcurves:
                    for keyframe_point in fcurve.keyframe_points:
                        keyframe_point.interpolation = self.config['interpolation_mode']
            
            bpy.ops.object.mode_set(mode='OBJECT')
            
            return {
                'success': True,
                'applied_keyframes': applied_keyframes,
                'total_keyframes': len(keyframes)
            }
            
        except Exception as e:
            logger.error(f"Failed to apply keyframes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _simulate_animation_creation(self, animation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate animation creation when Blender is not available."""
        motion = animation_request['motion']
        duration = motion.get('duration', self.config['default_duration'])
        frame_count = int(duration * self.config['frame_rate'])
        
        return {
            'success': True,
            'simulation_mode': True,
            'frame_count': frame_count,
            'linkage_type': animation_request['linkage_type'],
            'note': 'Animation simulated - Blender not available'
        }
    
    def update_animation_speed(self, speed_multiplier: float) -> Dict[str, Any]:
        """Update animation playback speed."""
        if not BLENDER_AVAILABLE:
            return {'success': True, 'note': 'Simulation mode'}
        
        if not self.current_animation:
            return {'success': False, 'error': 'No active animation'}
        
        # Scale frame range
        current_end = bpy.context.scene.frame_end
        new_end = int(current_end / speed_multiplier)
        
        bpy.context.scene.frame_end = max(1, new_end)
        
        return {
            'success': True,
            'new_frame_end': new_end,
            'speed_multiplier': speed_multiplier
        }
    
    def get_animation_info(self) -> Dict[str, Any]:
        """Get information about current animation."""
        if not self.current_animation:
            return {'active_animation': False}
        
        return {
            'active_animation': True,
            'linkage_type': self.current_animation['linkage_type'],
            'frame_count': self.current_animation['frame_count'],
            'parameters': self.current_animation['parameters'],
            'motion': self.current_animation['motion']
        }


if __name__ == "__main__":
    # Test the animator
    print("Testing Linkage Animator:")
    
    animator = LinkageAnimator()
    
    # Test animation request
    animation_request = {
        'linkage_type': 'four_bar',
        'parameters': {
            'ground_length': 10.0,
            'input_length': 3.0,
            'coupler_length': 8.0,
            'output_length': 5.0,
            'name': 'TestFourBar'
        },
        'motion': {
            'type': 'constant_rotation',
            'rpm': 60,
            'duration': 5.0
        }
    }
    
    if not BLENDER_AVAILABLE:
        # Run simulation test
        result = animator._simulate_animation_creation(animation_request)
        print(f"Simulation result: {result}")
    else:
        print("Blender available - full testing would require armature object") 