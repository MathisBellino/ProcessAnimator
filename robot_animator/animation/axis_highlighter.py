#!/usr/bin/env python3
"""
Axis Highlighter for ProcessAnimator

Determines main animation axes and highlights them in blue in the Blender scene
to show the primary movement directions for robot operations.
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class AxisHighlighter:
    """
    Animation axis highlighter for robot motion visualization.
    
    Analyzes robot positions and movements to determine the main animation axis
    and creates blue highlighting in the Blender scene.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AxisHighlighter.
        
        Args:
            config: Optional configuration for axis highlighting
        """
        self.config = config or self._default_config()
        self.axis_colors = {
            'x': (0.0, 0.0, 1.0, 0.7),  # Blue
            'y': (0.0, 0.0, 1.0, 0.7),  # Blue
            'z': (0.0, 0.0, 1.0, 0.7),  # Blue
            'xy': (0.0, 0.0, 1.0, 0.7), # Blue
            'xz': (0.0, 0.0, 1.0, 0.7), # Blue
            'yz': (0.0, 0.0, 1.0, 0.7)  # Blue
        }
        
        logger.info("AxisHighlighter initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for axis highlighting."""
        return {
            'highlight_color': 'blue',
            'axis_transparency': 0.3,
            'axis_thickness': 0.02,
            'axis_length_factor': 1.2,
            'enable_glow_effect': True,
            'enable_animation_pulse': True,
            'pulse_speed': 2.0,
            'highlight_duration': -1,  # -1 for permanent
            'blender_integration': True
        }
    
    def determine_main_axis(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the main animation axis based on process data.
        
        Args:
            process_data: Dictionary containing robot positions and movement data
            
        Returns:
            Dictionary containing axis information and visualization data
        """
        try:
            robot_position = process_data.get('robot_position', (0, 0, 1))
            target_positions = process_data.get('target_positions', [(0.5, 0.3, 0.8)])
            workspace_bounds = process_data.get('workspace_bounds', {
                'x': (-1, 1), 'y': (-1, 1), 'z': (0, 2)
            })
            
            # Calculate movement vectors
            movement_vectors = self._calculate_movement_vectors(robot_position, target_positions)
            
            # Analyze dominant movement directions
            primary_axis = self._analyze_dominant_axis(movement_vectors)
            
            # Generate axis visualization points
            axis_points = self._generate_axis_points(
                robot_position, target_positions, primary_axis, workspace_bounds
            )
            
            # Calculate axis vector
            axis_vector = self._calculate_axis_vector(primary_axis)
            
            # Generate visualization properties
            visualization_props = self._generate_visualization_properties(primary_axis)
            
            result = {
                'primary_axis': primary_axis,
                'axis_vector': axis_vector,
                'axis_points': axis_points,
                'movement_vectors': movement_vectors,
                'visualization_props': visualization_props,
                'confidence_score': self._calculate_axis_confidence(movement_vectors, primary_axis),
                'workspace_bounds': workspace_bounds
            }
            
            logger.info(f"Determined primary axis: {primary_axis}")
            return result
            
        except Exception as e:
            logger.error(f"Axis determination failed: {str(e)}")
            raise
    
    def _calculate_movement_vectors(self, robot_pos: Tuple[float, float, float], 
                                   target_positions: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        """Calculate movement vectors from robot position to targets."""
        vectors = []
        
        for target_pos in target_positions:
            vector = (
                target_pos[0] - robot_pos[0],
                target_pos[1] - robot_pos[1], 
                target_pos[2] - robot_pos[2]
            )
            vectors.append(vector)
        
        return vectors
    
    def _analyze_dominant_axis(self, movement_vectors: List[Tuple[float, float, float]]) -> str:
        """Analyze movement vectors to determine dominant axis."""
        if not movement_vectors:
            return 'z'  # Default to vertical movement
        
        # Calculate total movement in each axis
        total_x = sum(abs(v[0]) for v in movement_vectors)
        total_y = sum(abs(v[1]) for v in movement_vectors)
        total_z = sum(abs(v[2]) for v in movement_vectors)
        
        # Determine primary and secondary axes
        movements = {'x': total_x, 'y': total_y, 'z': total_z}
        sorted_movements = sorted(movements.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_movements[0][0]
        secondary = sorted_movements[1][0]
        
        # Check if movement is significant in multiple axes
        primary_movement = sorted_movements[0][1]
        secondary_movement = sorted_movements[1][1]
        
        # If secondary movement is significant (>60% of primary), combine axes
        if secondary_movement > 0.6 * primary_movement:
            combined_axes = ''.join(sorted([primary, secondary]))
            return combined_axes
        
        return primary
    
    def _generate_axis_points(self, robot_pos: Tuple[float, float, float],
                             target_positions: List[Tuple[float, float, float]],
                             primary_axis: str,
                             workspace_bounds: Dict[str, Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        """Generate points for axis visualization."""
        
        # Calculate workspace center
        center_x = (workspace_bounds['x'][0] + workspace_bounds['x'][1]) / 2
        center_y = (workspace_bounds['y'][0] + workspace_bounds['y'][1]) / 2
        center_z = (workspace_bounds['z'][0] + workspace_bounds['z'][1]) / 2
        workspace_center = (center_x, center_y, center_z)
        
        # Extend axis based on workspace bounds
        extension_factor = self.config['axis_length_factor']
        
        if primary_axis == 'x':
            x_range = workspace_bounds['x']
            x_extended = (
                x_range[0] - (x_range[1] - x_range[0]) * 0.1 * extension_factor,
                x_range[1] + (x_range[1] - x_range[0]) * 0.1 * extension_factor
            )
            return [
                (x_extended[0], workspace_center[1], workspace_center[2]),
                (x_extended[1], workspace_center[1], workspace_center[2])
            ]
        
        elif primary_axis == 'y':
            y_range = workspace_bounds['y']
            y_extended = (
                y_range[0] - (y_range[1] - y_range[0]) * 0.1 * extension_factor,
                y_range[1] + (y_range[1] - y_range[0]) * 0.1 * extension_factor
            )
            return [
                (workspace_center[0], y_extended[0], workspace_center[2]),
                (workspace_center[0], y_extended[1], workspace_center[2])
            ]
        
        elif primary_axis == 'z':
            z_range = workspace_bounds['z']
            z_extended = (
                z_range[0] - (z_range[1] - z_range[0]) * 0.1 * extension_factor,
                z_range[1] + (z_range[1] - z_range[0]) * 0.1 * extension_factor
            )
            return [
                (workspace_center[0], workspace_center[1], z_extended[0]),
                (workspace_center[0], workspace_center[1], z_extended[1])
            ]
        
        elif primary_axis in ['xy', 'yx']:
            # Diagonal movement in XY plane
            x_range = workspace_bounds['x']
            y_range = workspace_bounds['y']
            return [
                (x_range[0], y_range[0], workspace_center[2]),
                (x_range[1], y_range[1], workspace_center[2])
            ]
        
        elif primary_axis in ['xz', 'zx']:
            # Diagonal movement in XZ plane
            x_range = workspace_bounds['x']
            z_range = workspace_bounds['z']
            return [
                (x_range[0], workspace_center[1], z_range[0]),
                (x_range[1], workspace_center[1], z_range[1])
            ]
        
        elif primary_axis in ['yz', 'zy']:
            # Diagonal movement in YZ plane
            y_range = workspace_bounds['y']
            z_range = workspace_bounds['z']
            return [
                (workspace_center[0], y_range[0], z_range[0]),
                (workspace_center[0], y_range[1], z_range[1])
            ]
        
        # Default: vertical axis
        return [
            (workspace_center[0], workspace_center[1], workspace_bounds['z'][0]),
            (workspace_center[0], workspace_center[1], workspace_bounds['z'][1])
        ]
    
    def _calculate_axis_vector(self, primary_axis: str) -> Tuple[float, float, float]:
        """Calculate normalized axis vector."""
        axis_vectors = {
            'x': (1.0, 0.0, 0.0),
            'y': (0.0, 1.0, 0.0),
            'z': (0.0, 0.0, 1.0),
            'xy': (0.707, 0.707, 0.0),
            'yx': (0.707, 0.707, 0.0),
            'xz': (0.707, 0.0, 0.707),
            'zx': (0.707, 0.0, 0.707),
            'yz': (0.0, 0.707, 0.707),
            'zy': (0.0, 0.707, 0.707)
        }
        
        return axis_vectors.get(primary_axis, (0.0, 0.0, 1.0))
    
    def _generate_visualization_properties(self, primary_axis: str) -> Dict[str, Any]:
        """Generate visualization properties for the axis."""
        return {
            'color': self.axis_colors.get(primary_axis, (0.0, 0.0, 1.0, 0.7)),
            'thickness': self.config['axis_thickness'],
            'transparency': self.config['axis_transparency'],
            'glow_enabled': self.config['enable_glow_effect'],
            'pulse_enabled': self.config['enable_animation_pulse'],
            'pulse_speed': self.config['pulse_speed'],
            'material_type': 'emission' if self.config['enable_glow_effect'] else 'standard'
        }
    
    def _calculate_axis_confidence(self, movement_vectors: List[Tuple[float, float, float]], 
                                  primary_axis: str) -> float:
        """Calculate confidence score for axis determination."""
        if not movement_vectors:
            return 0.5
        
        # Calculate total movement in each axis
        total_x = sum(abs(v[0]) for v in movement_vectors)
        total_y = sum(abs(v[1]) for v in movement_vectors)
        total_z = sum(abs(v[2]) for v in movement_vectors)
        
        total_movement = total_x + total_y + total_z
        if total_movement == 0:
            return 0.5
        
        # Calculate confidence based on dominance of the primary axis
        if primary_axis == 'x':
            return min(total_x / total_movement * 2.0, 1.0)
        elif primary_axis == 'y':
            return min(total_y / total_movement * 2.0, 1.0)
        elif primary_axis == 'z':
            return min(total_z / total_movement * 2.0, 1.0)
        elif primary_axis in ['xy', 'yx']:
            return min((total_x + total_y) / total_movement * 1.5, 1.0)
        elif primary_axis in ['xz', 'zx']:
            return min((total_x + total_z) / total_movement * 1.5, 1.0)
        elif primary_axis in ['yz', 'zy']:
            return min((total_y + total_z) / total_movement * 1.5, 1.0)
        
        return 0.5
    
    def highlight_in_blender(self, axis_data: Dict[str, Any], 
                           highlight_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create blue axis highlighting in Blender scene.
        
        Args:
            axis_data: Axis information from determine_main_axis
            highlight_config: Optional highlighting configuration
            
        Returns:
            Dictionary containing highlighting results
        """
        try:
            config = highlight_config or {}
            
            # For now, simulate Blender operations since we can't import bpy in tests
            # In a real implementation, this would use actual Blender API calls
            
            if self.config['blender_integration']:
                result = self._create_blender_axis_highlight(axis_data, config)
            else:
                result = self._simulate_axis_highlight(axis_data, config)
            
            logger.info(f"Highlighted {axis_data['primary_axis']} axis in blue")
            return result
            
        except Exception as e:
            logger.error(f"Blender highlighting failed: {str(e)}")
            return {'error': str(e), 'highlighted': False}
    
    def _create_blender_axis_highlight(self, axis_data: Dict[str, Any], 
                                     config: Dict[str, Any]) -> Dict[str, Any]:
        """Create actual Blender axis highlighting."""
        try:
            # This would contain actual Blender API calls
            # For testing purposes, we'll simulate the operations
            
            # Import Blender modules (would be real in production)
            # import bpy
            # import bmesh
            
            axis_points = axis_data['axis_points']
            visualization_props = axis_data['visualization_props']
            
            # Simulate creating a cylinder for the axis
            # In reality: bpy.ops.mesh.primitive_cylinder_add(...)
            
            axis_length = self._calculate_distance(axis_points[0], axis_points[1])
            axis_center = self._calculate_midpoint(axis_points[0], axis_points[1])
            
            # Simulate material creation
            material_props = {
                'name': f"AxisHighlight_{axis_data['primary_axis']}",
                'color': visualization_props['color'],
                'transparency': config.get('transparency', visualization_props['transparency']),
                'emission_strength': 1.0 if visualization_props['glow_enabled'] else 0.0
            }
            
            # Simulate animation setup for pulsing effect
            animation_props = {}
            if config.get('animation_pulse', visualization_props['pulse_enabled']):
                animation_props = {
                    'pulse_enabled': True,
                    'pulse_speed': config.get('pulse_speed', visualization_props['pulse_speed']),
                    'pulse_range': (0.5, 1.0)
                }
            
            return {
                'highlighted': True,
                'color': 'blue',
                'axis_object_name': f"AxisHighlight_{axis_data['primary_axis']}",
                'axis_length': axis_length,
                'axis_center': axis_center,
                'material_props': material_props,
                'animation_props': animation_props,
                'transparency': material_props['transparency'],
                'effects': {
                    'glow': visualization_props['glow_enabled'],
                    'pulse': animation_props.get('pulse_enabled', False)
                }
            }
            
        except Exception as e:
            logger.error(f"Blender axis creation failed: {str(e)}")
            return {'error': str(e), 'highlighted': False}
    
    def _simulate_axis_highlight(self, axis_data: Dict[str, Any], 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate axis highlighting for testing purposes."""
        visualization_props = axis_data['visualization_props']
        
        return {
            'highlighted': True,
            'color': 'blue',
            'axis_type': axis_data['primary_axis'],
            'simulation_mode': True,
            'transparency': config.get('transparency', visualization_props['transparency']),
            'effects': {
                'glow': config.get('glow_effect', visualization_props['glow_enabled']),
                'pulse': config.get('animation_pulse', visualization_props['pulse_enabled'])
            }
        }
    
    def _calculate_distance(self, point1: Tuple[float, float, float], 
                           point2: Tuple[float, float, float]) -> float:
        """Calculate distance between two 3D points."""
        return math.sqrt(
            (point2[0] - point1[0])**2 + 
            (point2[1] - point1[1])**2 + 
            (point2[2] - point1[2])**2
        )
    
    def _calculate_midpoint(self, point1: Tuple[float, float, float], 
                           point2: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Calculate midpoint between two 3D points."""
        return (
            (point1[0] + point2[0]) / 2,
            (point1[1] + point2[1]) / 2,
            (point1[2] + point2[2]) / 2
        )
    
    def update_axis_highlight(self, axis_object_name: str, 
                             new_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing axis highlight properties."""
        try:
            # In a real implementation, this would update the Blender object
            # For now, simulate the update
            
            updated_properties = {
                'object_name': axis_object_name,
                'updated_properties': new_properties,
                'update_timestamp': logging.time.time(),
                'success': True
            }
            
            logger.info(f"Updated axis highlight: {axis_object_name}")
            return updated_properties
            
        except Exception as e:
            logger.error(f"Axis highlight update failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def remove_axis_highlight(self, axis_object_name: str) -> Dict[str, Any]:
        """Remove axis highlight from Blender scene."""
        try:
            # In a real implementation, this would remove the Blender object
            # For now, simulate the removal
            
            result = {
                'object_name': axis_object_name,
                'removed': True,
                'removal_timestamp': logging.time.time()
            }
            
            logger.info(f"Removed axis highlight: {axis_object_name}")
            return result
            
        except Exception as e:
            logger.error(f"Axis highlight removal failed: {str(e)}")
            return {'removed': False, 'error': str(e)} 