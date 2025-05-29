#!/usr/bin/env python3
"""
Smart Scaler for ProcessAnimator

Automatically scales entire assemblies based on a single reference dimension.
Users select one component, specify its real-world dimension, and the system
scales the entire assembly proportionally.
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
import bpy
import bmesh
import mathutils

logger = logging.getLogger(__name__)


class SmartScaler:
    """
    Intelligent assembly scaling system.
    
    Allows users to specify the real-world dimension of any component
    and automatically scales the entire assembly to match real proportions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SmartScaler.
        
        Args:
            config: Optional configuration for scaling behavior
        """
        self.config = config or self._default_config()
        self.scaling_history = []
        self.current_scale_factor = 1.0
        
        logger.info("SmartScaler initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for smart scaling."""
        return {
            'preserve_hierarchy': True,
            'scale_animations': True,
            'scale_constraints': True,
            'scale_physics': True,
            'auto_detect_assembly': True,
            'minimum_scale_factor': 0.001,
            'maximum_scale_factor': 1000.0,
            'precision_digits': 3
        }
    
    def scale_assembly(self, reference_object: str, real_dimension: float, 
                      measurement_axis: str = 'AUTO') -> Dict[str, Any]:
        """
        Scale entire assembly based on reference object dimension.
        
        Args:
            reference_object: Name of the reference object in Blender
            real_dimension: Real-world dimension in millimeters
            measurement_axis: Axis to measure ('X', 'Y', 'Z', or 'AUTO')
            
        Returns:
            Dictionary containing scaling results
        """
        try:
            # Get reference object
            ref_obj = bpy.data.objects.get(reference_object)
            if not ref_obj:
                return {'success': False, 'error': f'Object "{reference_object}" not found'}
            
            # Measure current dimension
            current_dimension = self._measure_object_dimension(ref_obj, measurement_axis)
            if current_dimension <= 0:
                return {'success': False, 'error': 'Could not measure object dimension'}
            
            # Calculate scale factor (convert mm to Blender units)
            blender_dimension = real_dimension / 1000.0  # mm to meters
            scale_factor = blender_dimension / current_dimension
            
            # Validate scale factor
            if not self._validate_scale_factor(scale_factor):
                return {
                    'success': False, 
                    'error': f'Scale factor {scale_factor:.3f} is outside valid range'
                }
            
            # Detect assembly components
            assembly_objects = self._detect_assembly_components(ref_obj)
            
            # Apply scaling
            scaling_result = self._apply_scaling(assembly_objects, scale_factor)
            
            # Update scaling history
            self._record_scaling_operation(ref_obj, real_dimension, scale_factor, assembly_objects)
            
            result = {
                'success': True,
                'scale_factor': scale_factor,
                'reference_object': reference_object,
                'real_dimension_mm': real_dimension,
                'measured_axis': measurement_axis,
                'scaled_objects': len(assembly_objects),
                'scaling_details': scaling_result
            }
            
            logger.info(f"Assembly scaled by factor {scale_factor:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Scaling failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _measure_object_dimension(self, obj: bpy.types.Object, axis: str) -> float:
        """Measure object dimension along specified axis."""
        
        # Ensure object has mesh data
        if obj.type != 'MESH':
            return 0.0
        
        # Get object bounds in world space
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        
        # Calculate dimensions
        min_x = min(corner.x for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)
        
        dimensions = {
            'X': max_x - min_x,
            'Y': max_y - min_y,
            'Z': max_z - min_z
        }
        
        if axis == 'AUTO':
            # Return the largest dimension
            return max(dimensions.values())
        elif axis in dimensions:
            return dimensions[axis]
        else:
            return 0.0
    
    def _validate_scale_factor(self, scale_factor: float) -> bool:
        """Validate that scale factor is within acceptable range."""
        return (self.config['minimum_scale_factor'] <= scale_factor <= 
                self.config['maximum_scale_factor'])
    
    def _detect_assembly_components(self, reference_object: bpy.types.Object) -> List[bpy.types.Object]:
        """
        Detect all components that should be scaled together.
        
        Uses multiple heuristics to identify related objects:
        - Parent-child relationships
        - Proximity analysis
        - Name pattern matching
        - Collection membership
        """
        assembly_objects = set()
        
        if self.config['auto_detect_assembly']:
            # Method 1: Include all objects in the same collection
            if reference_object.users_collection:
                for collection in reference_object.users_collection:
                    assembly_objects.update(collection.objects)
            
            # Method 2: Include parent-child hierarchy
            assembly_objects.update(self._get_hierarchy_objects(reference_object))
            
            # Method 3: Include objects with similar naming patterns
            assembly_objects.update(self._get_similar_named_objects(reference_object))
            
            # Method 4: Include nearby objects
            assembly_objects.update(self._get_nearby_objects(reference_object))
        
        # Always include the reference object
        assembly_objects.add(reference_object)
        
        # Filter out non-scalable objects
        scalable_objects = [obj for obj in assembly_objects if self._is_scalable(obj)]
        
        return scalable_objects
    
    def _get_hierarchy_objects(self, obj: bpy.types.Object) -> List[bpy.types.Object]:
        """Get all objects in the parent-child hierarchy."""
        hierarchy_objects = []
        
        # Get root parent
        root = obj
        while root.parent:
            root = root.parent
        
        # Recursively collect all children
        def collect_children(parent_obj):
            hierarchy_objects.append(parent_obj)
            for child in parent_obj.children:
                collect_children(child)
        
        collect_children(root)
        return hierarchy_objects
    
    def _get_similar_named_objects(self, obj: bpy.types.Object) -> List[bpy.types.Object]:
        """Get objects with similar naming patterns."""
        similar_objects = []
        obj_name = obj.name.lower()
        
        # Extract base name (remove numbers and common suffixes)
        base_patterns = [
            obj_name.split('.')[0],  # Remove .001, .002 etc.
            obj_name.split('_')[0],  # Remove _part1, _part2 etc.
            obj_name.rstrip('0123456789'),  # Remove trailing numbers
        ]
        
        for scene_obj in bpy.context.scene.objects:
            scene_name = scene_obj.name.lower()
            for pattern in base_patterns:
                if pattern and len(pattern) > 2 and pattern in scene_name:
                    similar_objects.append(scene_obj)
                    break
        
        return similar_objects
    
    def _get_nearby_objects(self, obj: bpy.types.Object, proximity_threshold: float = 5.0) -> List[bpy.types.Object]:
        """Get objects within proximity threshold."""
        nearby_objects = []
        obj_location = obj.matrix_world.translation
        
        for scene_obj in bpy.context.scene.objects:
            if scene_obj == obj:
                continue
            
            distance = (scene_obj.matrix_world.translation - obj_location).length
            if distance <= proximity_threshold:
                nearby_objects.append(scene_obj)
        
        return nearby_objects
    
    def _is_scalable(self, obj: bpy.types.Object) -> bool:
        """Check if object should be scaled."""
        # Don't scale cameras, lights, empties used as constraints
        if obj.type in ['CAMERA', 'LIGHT', 'SPEAKER']:
            return False
        
        # Don't scale objects marked as non-scalable
        if 'no_scale' in obj.keys():
            return False
        
        return True
    
    def _apply_scaling(self, objects: List[bpy.types.Object], scale_factor: float) -> Dict[str, Any]:
        """Apply scaling to all objects in the assembly."""
        
        scaling_details = {
            'scaled_objects': [],
            'scaled_animations': [],
            'scaled_constraints': [],
            'failed_objects': []
        }
        
        # Store original selection and active object
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.active_object
        
        try:
            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')
            
            for obj in objects:
                try:
                    # Select and make active
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    
                    # Apply scaling
                    bpy.ops.transform.resize(value=(scale_factor, scale_factor, scale_factor))
                    
                    # Scale animations if enabled
                    if self.config['scale_animations'] and obj.animation_data:
                        self._scale_object_animation(obj, scale_factor)
                        scaling_details['scaled_animations'].append(obj.name)
                    
                    # Scale constraints if enabled
                    if self.config['scale_constraints']:
                        self._scale_object_constraints(obj, scale_factor)
                        scaling_details['scaled_constraints'].append(obj.name)
                    
                    scaling_details['scaled_objects'].append(obj.name)
                    obj.select_set(False)
                    
                except Exception as e:
                    logger.warning(f"Failed to scale object {obj.name}: {str(e)}")
                    scaling_details['failed_objects'].append({'name': obj.name, 'error': str(e)})
            
            # Update current scale factor
            self.current_scale_factor *= scale_factor
            
        finally:
            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                if obj:
                    obj.select_set(True)
            
            if original_active:
                bpy.context.view_layer.objects.active = original_active
        
        return scaling_details
    
    def _scale_object_animation(self, obj: bpy.types.Object, scale_factor: float):
        """Scale object animations (keyframes) to match new size."""
        if not obj.animation_data or not obj.animation_data.action:
            return
        
        action = obj.animation_data.action
        
        for fcurve in action.fcurves:
            # Scale location keyframes
            if fcurve.data_path == 'location':
                for keyframe in fcurve.keyframe_points:
                    keyframe.co.y *= scale_factor
                    keyframe.handle_left.y *= scale_factor
                    keyframe.handle_right.y *= scale_factor
    
    def _scale_object_constraints(self, obj: bpy.types.Object, scale_factor: float):
        """Scale object constraints to match new size."""
        for constraint in obj.constraints:
            # Scale distance constraints
            if hasattr(constraint, 'distance'):
                constraint.distance *= scale_factor
            
            # Scale limit constraints
            if hasattr(constraint, 'max_x'):
                constraint.max_x *= scale_factor
                constraint.min_x *= scale_factor
            if hasattr(constraint, 'max_y'):
                constraint.max_y *= scale_factor
                constraint.min_y *= scale_factor
            if hasattr(constraint, 'max_z'):
                constraint.max_z *= scale_factor
                constraint.min_z *= scale_factor
    
    def _record_scaling_operation(self, reference_obj: bpy.types.Object, 
                                 real_dimension: float, scale_factor: float, 
                                 scaled_objects: List[bpy.types.Object]):
        """Record scaling operation for history tracking."""
        operation = {
            'timestamp': bpy.context.scene.frame_current,  # Use frame as timestamp
            'reference_object': reference_obj.name,
            'real_dimension_mm': real_dimension,
            'scale_factor': scale_factor,
            'scaled_objects': [obj.name for obj in scaled_objects],
            'cumulative_scale': self.current_scale_factor
        }
        
        self.scaling_history.append(operation)
    
    def get_scaling_info(self) -> Dict[str, Any]:
        """Get current scaling information."""
        return {
            'current_scale_factor': self.current_scale_factor,
            'scaling_history': self.scaling_history,
            'total_operations': len(self.scaling_history)
        }
    
    def reset_scaling(self) -> Dict[str, Any]:
        """Reset all scaling to original size."""
        try:
            # Calculate inverse scale factor
            if self.current_scale_factor == 0:
                return {'success': False, 'error': 'Cannot reset: invalid current scale factor'}
            
            inverse_scale = 1.0 / self.current_scale_factor
            
            # Get all objects that were scaled
            all_scaled_objects = set()
            for operation in self.scaling_history:
                for obj_name in operation['scaled_objects']:
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        all_scaled_objects.add(obj)
            
            # Apply inverse scaling
            if all_scaled_objects:
                scaling_result = self._apply_scaling(list(all_scaled_objects), inverse_scale)
                
                # Reset state
                self.current_scale_factor = 1.0
                self.scaling_history.clear()
                
                return {
                    'success': True,
                    'reset_objects': len(all_scaled_objects),
                    'scaling_details': scaling_result
                }
            else:
                return {'success': False, 'error': 'No scaled objects found to reset'}
                
        except Exception as e:
            logger.error(f"Reset scaling failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def auto_scale_from_real_dimensions(self, dimension_pairs: List[Tuple[str, float]]) -> Dict[str, Any]:
        """
        Auto-scale based on multiple known real dimensions.
        
        Args:
            dimension_pairs: List of (object_name, real_dimension_mm) tuples
            
        Returns:
            Dictionary containing auto-scaling results
        """
        if not dimension_pairs:
            return {'success': False, 'error': 'No dimension pairs provided'}
        
        try:
            scale_factors = []
            
            # Calculate scale factor for each known dimension
            for obj_name, real_dimension in dimension_pairs:
                obj = bpy.data.objects.get(obj_name)
                if not obj:
                    continue
                
                current_dimension = self._measure_object_dimension(obj, 'AUTO')
                if current_dimension > 0:
                    blender_dimension = real_dimension / 1000.0  # mm to meters
                    scale_factor = blender_dimension / current_dimension
                    scale_factors.append(scale_factor)
            
            if not scale_factors:
                return {'success': False, 'error': 'Could not calculate scale factors'}
            
            # Use average scale factor
            avg_scale_factor = sum(scale_factors) / len(scale_factors)
            
            # Apply scaling using first object as reference
            ref_obj_name = dimension_pairs[0][0]
            result = self.scale_assembly(ref_obj_name, dimension_pairs[0][1], 'AUTO')
            
            result['auto_scale_info'] = {
                'calculated_scale_factors': scale_factors,
                'average_scale_factor': avg_scale_factor,
                'scale_factor_variance': max(scale_factors) - min(scale_factors)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Auto-scaling failed: {str(e)}")
            return {'success': False, 'error': str(e)} 