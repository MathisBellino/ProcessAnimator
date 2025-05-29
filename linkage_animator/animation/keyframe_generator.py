#!/usr/bin/env python3
"""
Keyframe Generator for Linkage Animations

Specialized keyframe generation with:
- Smooth interpolation between positions
- Optimized keyframe placement
- Motion path calculation
- Constraint-aware animation
"""

import math
import logging
from typing import Dict, Any, List, Tuple, Optional

try:
    import bpy
    from mathutils import Vector, Euler, Quaternion
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

logger = logging.getLogger(__name__)


class KeyframeGenerator:
    """
    Advanced keyframe generator for linkage mechanisms.
    
    Generates optimized keyframe sequences that produce smooth,
    realistic motion while respecting mechanical constraints.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize keyframe generator.
        
        Args:
            config: Optional configuration for keyframe generation
        """
        self.config = config or self._default_config()
        self.motion_cache = {}
        
        logger.info("Keyframe generator initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for keyframe generation."""
        return {
            'interpolation_type': 'BEZIER',
            'keyframe_reduction': True,
            'max_keyframes_per_bone': 100,
            'smoothing_factor': 0.8,
            'velocity_continuity': True,
            'adaptive_sampling': True,
            'constraint_compliance': True,
            'motion_blur_support': True
        }
    
    def generate_linkage_animation(self, animation_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate complete keyframe animation for a linkage mechanism.
        
        Args:
            animation_config: Animation configuration parameters
            
        Returns:
            List of keyframe dictionaries
        """
        try:
            linkage_type = animation_config['linkage_type']
            input_motion = animation_config['input_motion']
            frame_rate = animation_config.get('frame_rate', 24)
            
            # Calculate total frames
            duration_frames = input_motion['duration']
            if isinstance(duration_frames, float):
                # Convert seconds to frames
                duration_frames = int(duration_frames * frame_rate)
            
            # Generate motion path
            motion_path = self._calculate_motion_path(linkage_type, input_motion, duration_frames)
            
            # Create keyframes from motion path
            keyframes = self._create_keyframes_from_path(motion_path, linkage_type)
            
            # Optimize keyframes
            if self.config['keyframe_reduction']:
                keyframes = self._optimize_keyframes(keyframes)
            
            # Apply smoothing
            if self.config['velocity_continuity']:
                keyframes = self._apply_smoothing(keyframes)
            
            return keyframes
            
        except Exception as e:
            logger.error(f"Keyframe generation failed: {e}")
            return []
    
    def _calculate_motion_path(self, linkage_type: str, input_motion: Dict[str, Any], 
                             total_frames: int) -> Dict[str, Any]:
        """Calculate motion path for the linkage mechanism."""
        
        # Cache key for motion calculations
        cache_key = f"{linkage_type}_{hash(str(input_motion))}_{total_frames}"
        
        if cache_key in self.motion_cache:
            return self.motion_cache[cache_key]
        
        motion_type = input_motion['type']
        start_angle = math.radians(input_motion.get('start_angle', 0))
        end_angle = math.radians(input_motion.get('end_angle', 360))
        
        # Generate motion samples
        motion_samples = []
        
        for frame in range(total_frames):
            progress = frame / (total_frames - 1) if total_frames > 1 else 0
            
            if motion_type == 'rotation':
                # Linear rotation interpolation
                current_angle = start_angle + progress * (end_angle - start_angle)
                
                # Add some easing for more natural motion
                if self.config['smoothing_factor'] > 0:
                    # Smooth step function
                    eased_progress = progress * progress * (3.0 - 2.0 * progress)
                    current_angle = start_angle + eased_progress * (end_angle - start_angle)
                
            elif motion_type == 'oscillation':
                # Sinusoidal oscillation
                frequency = input_motion.get('frequency', 1.0)
                amplitude = input_motion.get('amplitude', math.pi)
                current_angle = amplitude * math.sin(2 * math.pi * frequency * progress)
                
            elif motion_type == 'custom':
                # Custom motion curve (placeholder)
                current_angle = start_angle + progress * (end_angle - start_angle)
                
            else:
                current_angle = start_angle
            
            motion_samples.append({
                'frame': frame + 1,
                'angle': current_angle,
                'progress': progress
            })
        
        motion_path = {
            'samples': motion_samples,
            'total_frames': total_frames,
            'linkage_type': linkage_type
        }
        
        # Cache the result
        self.motion_cache[cache_key] = motion_path
        
        return motion_path
    
    def _create_keyframes_from_path(self, motion_path: Dict[str, Any], 
                                  linkage_type: str) -> List[Dict[str, Any]]:
        """Create keyframes from calculated motion path."""
        keyframes = []
        samples = motion_path['samples']
        
        # Adaptive sampling - place more keyframes where motion changes rapidly
        if self.config['adaptive_sampling']:
            selected_frames = self._adaptive_frame_selection(samples)
        else:
            # Uniform sampling
            step = max(1, len(samples) // self.config['max_keyframes_per_bone'])
            selected_frames = range(0, len(samples), step)
        
        for frame_idx in selected_frames:
            if frame_idx >= len(samples):
                continue
                
            sample = samples[frame_idx]
            frame_number = sample['frame']
            input_angle = sample['angle']
            
            # Create keyframes for different linkage types
            if linkage_type == 'four_bar':
                bone_keyframes = self._create_four_bar_keyframes(frame_number, input_angle)
            elif linkage_type == 'slider_crank':
                bone_keyframes = self._create_slider_crank_keyframes(frame_number, input_angle)
            else:
                bone_keyframes = []
            
            keyframes.extend(bone_keyframes)
        
        return keyframes
    
    def _adaptive_frame_selection(self, samples: List[Dict[str, Any]]) -> List[int]:
        """Select frames adaptively based on motion complexity."""
        selected_indices = [0]  # Always include first frame
        
        if len(samples) < 3:
            return list(range(len(samples)))
        
        # Calculate motion complexity (rate of change)
        for i in range(1, len(samples) - 1):
            prev_angle = samples[i-1]['angle']
            curr_angle = samples[i]['angle']
            next_angle = samples[i+1]['angle']
            
            # Calculate second derivative (acceleration)
            acceleration = abs((next_angle - curr_angle) - (curr_angle - prev_angle))
            
            # Select frame if acceleration is above threshold
            if acceleration > 0.01:  # Threshold for significant motion change
                selected_indices.append(i)
        
        # Always include last frame
        selected_indices.append(len(samples) - 1)
        
        # Remove duplicates and sort
        selected_indices = sorted(list(set(selected_indices)))
        
        # Limit total number of keyframes
        if len(selected_indices) > self.config['max_keyframes_per_bone']:
            # Keep evenly distributed subset
            step = len(selected_indices) // self.config['max_keyframes_per_bone']
            selected_indices = selected_indices[::step]
        
        return selected_indices
    
    def _create_four_bar_keyframes(self, frame_number: int, input_angle: float) -> List[Dict[str, Any]]:
        """Create keyframes for four-bar linkage at specific input angle."""
        keyframes = []
        
        # Input link keyframe
        keyframes.append({
            'bone_name': 'input_link',
            'frame': frame_number,
            'rotation': (0, 0, input_angle),
            'rotation_mode': 'XYZ',
            'interpolation': self.config['interpolation_type']
        })
        
        # For a complete implementation, we would calculate coupler and output angles
        # using the linkage kinematics. For now, using simplified relationships.
        
        # Simplified coupler angle (this would use actual kinematic calculations)
        coupler_angle = input_angle * 0.7 + math.sin(input_angle) * 0.3
        keyframes.append({
            'bone_name': 'coupler_link',
            'frame': frame_number,
            'rotation': (0, 0, coupler_angle),
            'rotation_mode': 'XYZ',
            'interpolation': self.config['interpolation_type']
        })
        
        # Simplified output angle
        output_angle = input_angle * 0.5 + math.cos(input_angle * 1.5) * 0.2
        keyframes.append({
            'bone_name': 'output_link',
            'frame': frame_number,
            'rotation': (0, 0, output_angle),
            'rotation_mode': 'XYZ',
            'interpolation': self.config['interpolation_type']
        })
        
        return keyframes
    
    def _create_slider_crank_keyframes(self, frame_number: int, crank_angle: float) -> List[Dict[str, Any]]:
        """Create keyframes for slider-crank mechanism."""
        keyframes = []
        
        # Crank rotation keyframe
        keyframes.append({
            'bone_name': 'crank',
            'frame': frame_number,
            'rotation': (0, 0, crank_angle),
            'rotation_mode': 'XYZ',
            'interpolation': self.config['interpolation_type']
        })
        
        # Connecting rod angle (simplified calculation)
        # In full implementation, this would use proper slider-crank kinematics
        rod_angle = math.sin(crank_angle) * 0.3
        keyframes.append({
            'bone_name': 'connecting_rod',
            'frame': frame_number,
            'rotation': (0, 0, rod_angle),
            'rotation_mode': 'XYZ',
            'interpolation': self.config['interpolation_type']
        })
        
        # Slider position (if using target object)
        crank_length = 2.0  # This should come from mechanism parameters
        connecting_rod_length = 6.0
        
        # Calculate slider position
        crank_pin_x = crank_length * math.cos(crank_angle)
        crank_pin_y = crank_length * math.sin(crank_angle)
        
        # Slider X position
        slider_x = crank_pin_x + math.sqrt(connecting_rod_length**2 - crank_pin_y**2)
        
        keyframes.append({
            'target_name': 'slider_target',
            'frame': frame_number,
            'location': (slider_x, 0, 0),
            'interpolation': self.config['interpolation_type']
        })
        
        return keyframes
    
    def _optimize_keyframes(self, keyframes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize keyframe placement to reduce redundancy."""
        if not keyframes:
            return keyframes
        
        # Group keyframes by bone/target
        bone_groups = {}
        for kf in keyframes:
            key = kf.get('bone_name') or kf.get('target_name', 'unknown')
            if key not in bone_groups:
                bone_groups[key] = []
            bone_groups[key].append(kf)
        
        optimized_keyframes = []
        
        for bone_name, bone_keyframes in bone_groups.items():
            if len(bone_keyframes) <= 2:
                # Keep all keyframes if there are only a few
                optimized_keyframes.extend(bone_keyframes)
                continue
            
            # Sort by frame number
            bone_keyframes.sort(key=lambda x: x['frame'])
            
            # Always keep first and last keyframes
            reduced_keyframes = [bone_keyframes[0]]
            
            # Apply Douglas-Peucker-like algorithm for keyframe reduction
            for i in range(1, len(bone_keyframes) - 1):
                prev_kf = bone_keyframes[i-1]
                curr_kf = bone_keyframes[i]
                next_kf = bone_keyframes[i+1]
                
                # Check if current keyframe is necessary
                if self._is_keyframe_necessary(prev_kf, curr_kf, next_kf):
                    reduced_keyframes.append(curr_kf)
            
            # Always keep last keyframe
            reduced_keyframes.append(bone_keyframes[-1])
            
            optimized_keyframes.extend(reduced_keyframes)
        
        logger.info(f"Keyframe optimization: {len(keyframes)} → {len(optimized_keyframes)}")
        return optimized_keyframes
    
    def _is_keyframe_necessary(self, prev_kf: Dict[str, Any], curr_kf: Dict[str, Any], 
                             next_kf: Dict[str, Any]) -> bool:
        """Determine if a keyframe is necessary for smooth motion."""
        
        # Check rotation keyframes
        if 'rotation' in curr_kf:
            prev_rot = prev_kf.get('rotation', (0, 0, 0))
            curr_rot = curr_kf.get('rotation', (0, 0, 0))
            next_rot = next_kf.get('rotation', (0, 0, 0))
            
            # Calculate interpolated value
            frame_diff = next_kf['frame'] - prev_kf['frame']
            if frame_diff == 0:
                return False
            
            t = (curr_kf['frame'] - prev_kf['frame']) / frame_diff
            
            interpolated_rot = tuple(
                prev_rot[i] + t * (next_rot[i] - prev_rot[i])
                for i in range(3)
            )
            
            # Check if current rotation differs significantly from interpolated
            threshold = 0.05  # radians
            for i in range(3):
                if abs(curr_rot[i] - interpolated_rot[i]) > threshold:
                    return True
        
        # Check location keyframes
        if 'location' in curr_kf:
            prev_loc = prev_kf.get('location', (0, 0, 0))
            curr_loc = curr_kf.get('location', (0, 0, 0))
            next_loc = next_kf.get('location', (0, 0, 0))
            
            frame_diff = next_kf['frame'] - prev_kf['frame']
            if frame_diff == 0:
                return False
            
            t = (curr_kf['frame'] - prev_kf['frame']) / frame_diff
            
            interpolated_loc = tuple(
                prev_loc[i] + t * (next_loc[i] - prev_loc[i])
                for i in range(3)
            )
            
            # Check if current location differs significantly
            threshold = 0.01  # units
            for i in range(3):
                if abs(curr_loc[i] - interpolated_loc[i]) > threshold:
                    return True
        
        return False
    
    def _apply_smoothing(self, keyframes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply smoothing to keyframes for better motion continuity."""
        if not self.config['velocity_continuity']:
            return keyframes
        
        # Group keyframes by bone
        bone_groups = {}
        for kf in keyframes:
            key = kf.get('bone_name') or kf.get('target_name', 'unknown')
            if key not in bone_groups:
                bone_groups[key] = []
            bone_groups[key].append(kf)
        
        smoothed_keyframes = []
        
        for bone_name, bone_keyframes in bone_groups.items():
            if len(bone_keyframes) < 3:
                smoothed_keyframes.extend(bone_keyframes)
                continue
            
            # Sort by frame
            bone_keyframes.sort(key=lambda x: x['frame'])
            
            # Apply smoothing to rotation values
            for i in range(1, len(bone_keyframes) - 1):
                prev_kf = bone_keyframes[i-1]
                curr_kf = bone_keyframes[i]
                next_kf = bone_keyframes[i+1]
                
                if 'rotation' in curr_kf:
                    smoothed_rotation = self._smooth_rotation(
                        prev_kf.get('rotation', (0, 0, 0)),
                        curr_kf.get('rotation', (0, 0, 0)),
                        next_kf.get('rotation', (0, 0, 0))
                    )
                    curr_kf['rotation'] = smoothed_rotation
                
                if 'location' in curr_kf:
                    smoothed_location = self._smooth_location(
                        prev_kf.get('location', (0, 0, 0)),
                        curr_kf.get('location', (0, 0, 0)),
                        next_kf.get('location', (0, 0, 0))
                    )
                    curr_kf['location'] = smoothed_location
            
            smoothed_keyframes.extend(bone_keyframes)
        
        return smoothed_keyframes
    
    def _smooth_rotation(self, prev_rot: Tuple[float, float, float],
                        curr_rot: Tuple[float, float, float],
                        next_rot: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Apply smoothing to rotation values."""
        smoothing = self.config['smoothing_factor']
        
        smoothed = []
        for i in range(3):
            # Simple moving average
            avg = (prev_rot[i] + next_rot[i]) / 2
            smoothed_value = curr_rot[i] * (1 - smoothing) + avg * smoothing
            smoothed.append(smoothed_value)
        
        return tuple(smoothed)
    
    def _smooth_location(self, prev_loc: Tuple[float, float, float],
                        curr_loc: Tuple[float, float, float],
                        next_loc: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Apply smoothing to location values."""
        smoothing = self.config['smoothing_factor']
        
        smoothed = []
        for i in range(3):
            avg = (prev_loc[i] + next_loc[i]) / 2
            smoothed_value = curr_loc[i] * (1 - smoothing) + avg * smoothing
            smoothed.append(smoothed_value)
        
        return tuple(smoothed)
    
    def create_motion_path_visualization(self, motion_path: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create visualization objects for motion paths."""
        if not BLENDER_AVAILABLE:
            return []
        
        path_objects = []
        samples = motion_path['samples']
        
        # Create curve object for motion path
        curve_data = bpy.data.curves.new('motion_path', type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create spline
        spline = curve_data.splines.new('NURBS')
        spline.points.add(len(samples) - 1)
        
        for i, sample in enumerate(samples):
            angle = sample['angle']
            # Simple circular path for visualization
            x = 2 * math.cos(angle)
            y = 2 * math.sin(angle)
            z = 0
            
            spline.points[i].co = (x, y, z, 1)
        
        # Create object
        curve_obj = bpy.data.objects.new('motion_path', curve_data)
        bpy.context.collection.objects.link(curve_obj)
        
        path_objects.append({
            'object': curve_obj,
            'type': 'motion_path'
        })
        
        return path_objects
    
    def get_keyframe_statistics(self, keyframes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about generated keyframes."""
        if not keyframes:
            return {'total_keyframes': 0}
        
        bone_counts = {}
        frame_range = [float('inf'), 0]
        
        for kf in keyframes:
            bone_name = kf.get('bone_name') or kf.get('target_name', 'unknown')
            bone_counts[bone_name] = bone_counts.get(bone_name, 0) + 1
            
            frame = kf['frame']
            frame_range[0] = min(frame_range[0], frame)
            frame_range[1] = max(frame_range[1], frame)
        
        return {
            'total_keyframes': len(keyframes),
            'bones_animated': len(bone_counts),
            'bone_keyframe_counts': bone_counts,
            'frame_range': frame_range,
            'average_keyframes_per_bone': len(keyframes) / len(bone_counts) if bone_counts else 0
        }


if __name__ == "__main__":
    # Test keyframe generator
    print("Testing Keyframe Generator:")
    
    generator = KeyframeGenerator()
    
    # Test configuration
    animation_config = {
        'linkage_type': 'four_bar',
        'input_motion': {
            'type': 'rotation',
            'start_angle': 0,
            'end_angle': 360,
            'duration': 120  # frames
        },
        'frame_rate': 24
    }
    
    keyframes = generator.generate_linkage_animation(animation_config)
    stats = generator.get_keyframe_statistics(keyframes)
    
    print(f"Generated keyframes: {stats}")
    print(f"Sample keyframes: {keyframes[:3] if keyframes else 'None'}") 