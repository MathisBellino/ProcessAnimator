#!/usr/bin/env python3
"""
GCODE Generator for ProcessAnimator

Converts Blender animations into real robot GCODE for physical execution.
Bridges the gap between simulation and reality with proper safety and
motion planning considerations.
"""

import logging
import math
import os
from typing import Dict, Any, List, Tuple, Optional
import bpy
import mathutils
from mathutils import Vector, Euler, Matrix

logger = logging.getLogger(__name__)


class GCodeGenerator:
    """
    GCODE generation system for robot animation to real-world execution.
    
    Converts Blender keyframe animations into robot-specific GCODE
    with proper safety checks, motion planning, and coordinate transformations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GCodeGenerator.
        
        Args:
            config: Optional configuration for GCODE generation
        """
        self.config = config or self._default_config()
        self.robot_profiles = self._load_robot_profiles()
        self.coordinate_systems = self._setup_coordinate_systems()
        
        logger.info("GCodeGenerator initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for GCODE generation."""
        return {
            'output_format': 'standard_gcode',
            'coordinate_system': 'world',
            'units': 'mm',
            'speed_units': 'mm/min',
            'safety_checks': True,
            'include_comments': True,
            'include_safety_stops': True,
            'motion_smoothing': True,
            'optimize_path': True,
            'max_linear_speed': 1000,  # mm/min
            'max_joint_speed': 50,     # deg/s
            'acceleration_limit': 500,  # mm/s²
            'coordinate_precision': 3   # decimal places
        }
    
    def _load_robot_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load robot-specific GCODE profiles."""
        return {
            'ABB_IRB6700': {
                'language': 'RAPID',
                'coordinate_system': 'robot_base',
                'home_position': [0, -90, 0, 0, 90, 0],  # joint angles in degrees
                'safe_position': [0, -45, 45, 0, 45, 0],
                'tool_offset': [0, 0, 200],  # mm from flange
                'commands': {
                    'move_joint': 'MoveJ',
                    'move_linear': 'MoveL',
                    'move_circular': 'MoveC',
                    'set_speed': 'v',
                    'set_zone': 'z',
                    'set_tool': 'PERS tooldata',
                    'wait': 'WaitTime'
                },
                'file_extension': '.mod',
                'header_template': 'abb_rapid_header.txt'
            },
            'KUKA_KR16': {
                'language': 'KRL',
                'coordinate_system': 'robot_base',
                'home_position': [0, -90, 90, 0, 90, 0],
                'safe_position': [0, -45, 45, 0, 45, 0],
                'tool_offset': [0, 0, 150],
                'commands': {
                    'move_joint': 'PTP',
                    'move_linear': 'LIN',
                    'move_circular': 'CIRC',
                    'set_speed': '$VEL.CP',
                    'set_acceleration': '$ACC.CP',
                    'set_tool': '$TOOL',
                    'wait': 'WAIT SEC'
                },
                'file_extension': '.src',
                'header_template': 'kuka_krl_header.txt'
            },
            'UR10': {
                'language': 'URScript',
                'coordinate_system': 'base',
                'home_position': [0, -90, 0, -90, 0, 0],
                'safe_position': [0, -45, -45, -90, 0, 0],
                'tool_offset': [0, 0, 100],
                'commands': {
                    'move_joint': 'movej',
                    'move_linear': 'movel',
                    'move_circular': 'movec',
                    'set_speed': 'speed',
                    'set_acceleration': 'accel',
                    'set_tcp': 'set_tcp',
                    'wait': 'sleep'
                },
                'file_extension': '.script',
                'header_template': 'ur_script_header.txt'
            },
            'FANUC_M20': {
                'language': 'KAREL',
                'coordinate_system': 'world',
                'home_position': [0, 0, 90, 0, 90, 0],
                'safe_position': [0, 0, 45, 0, 45, 0],
                'tool_offset': [0, 0, 175],
                'commands': {
                    'move_joint': 'J P',
                    'move_linear': 'L P',
                    'move_circular': 'C P',
                    'set_speed': 'CNT',
                    'set_tool': 'UTOOL_NUM',
                    'wait': 'WAIT'
                },
                'file_extension': '.ls',
                'header_template': 'fanuc_karel_header.txt'
            },
            'GENERIC': {
                'language': 'GCODE',
                'coordinate_system': 'world',
                'home_position': [0, 0, 0, 0, 0, 0],
                'safe_position': [0, 0, 100, 0, 0, 0],  # mm and degrees
                'tool_offset': [0, 0, 100],
                'commands': {
                    'move_joint': 'G0',
                    'move_linear': 'G1',
                    'move_circular': 'G2',
                    'set_speed': 'F',
                    'set_tool': 'T',
                    'wait': 'G4 P'
                },
                'file_extension': '.gcode',
                'header_template': 'generic_gcode_header.txt'
            }
        }
    
    def _setup_coordinate_systems(self) -> Dict[str, Dict[str, Any]]:
        """Setup coordinate system transformations."""
        return {
            'blender_to_robot': {
                'scale_factor': 1000.0,  # Blender units (m) to robot units (mm)
                'rotation_matrix': Matrix.Rotation(math.radians(-90), 4, 'X'),  # Blender Z-up to robot Y-up
                'origin_offset': Vector((0, 0, 0))
            },
            'robot_to_world': {
                'scale_factor': 1.0,
                'rotation_matrix': Matrix.Identity(4),
                'origin_offset': Vector((0, 0, 0))
            }
        }
    
    def generate_from_animation(self, output_path: str, robot_type: str = 'GENERIC') -> Dict[str, Any]:
        """
        Generate GCODE from current Blender animation.
        
        Args:
            output_path: Path to save the generated GCODE file
            robot_type: Type of robot for GCODE generation
            
        Returns:
            Dictionary containing generation results
        """
        try:
            # Validate robot type
            if robot_type not in self.robot_profiles:
                robot_type = 'GENERIC'
            
            robot_profile = self.robot_profiles[robot_type]
            
            # Extract animation data
            animation_data = self._extract_animation_data()
            if not animation_data['success']:
                return animation_data
            
            # Convert to robot coordinates
            robot_coordinates = self._convert_to_robot_coordinates(
                animation_data['keyframes'], robot_profile
            )
            
            # Generate motion path
            motion_path = self._generate_motion_path(robot_coordinates, robot_profile)
            
            # Optimize path if enabled
            if self.config['optimize_path']:
                motion_path = self._optimize_motion_path(motion_path, robot_profile)
            
            # Generate GCODE
            gcode_content = self._generate_gcode_content(motion_path, robot_profile)
            
            # Add safety checks
            if self.config['safety_checks']:
                gcode_content = self._add_safety_checks(gcode_content, robot_profile)
            
            # Write to file
            output_file = self._write_gcode_file(gcode_content, output_path, robot_profile)
            
            result = {
                'success': True,
                'output_file': output_file,
                'robot_type': robot_type,
                'language': robot_profile['language'],
                'total_moves': len(motion_path),
                'estimated_execution_time': self._estimate_execution_time(motion_path),
                'file_size_bytes': os.path.getsize(output_file) if os.path.exists(output_file) else 0
            }
            
            logger.info(f"Generated GCODE for {robot_type}: {output_file}")
            return result
            
        except Exception as e:
            logger.error(f"GCODE generation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_animation_data(self) -> Dict[str, Any]:
        """Extract keyframe data from Blender animation."""
        
        # Find robot armature or object
        robot_object = self._find_robot_object()
        if not robot_object:
            return {'success': False, 'error': 'No robot object found in scene'}
        
        # Get animation frame range
        scene = bpy.context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        frame_step = 1
        
        keyframes = []
        
        # Extract keyframes for each frame
        for frame in range(frame_start, frame_end + 1, frame_step):
            scene.frame_set(frame)
            
            if robot_object.type == 'ARMATURE':
                # Extract bone transformations
                bone_data = self._extract_bone_transformations(robot_object)
                keyframes.append({
                    'frame': frame,
                    'timestamp': frame / scene.render.fps,
                    'type': 'armature',
                    'data': bone_data
                })
            else:
                # Extract object transformation
                transform_data = self._extract_object_transformation(robot_object)
                keyframes.append({
                    'frame': frame,
                    'timestamp': frame / scene.render.fps,
                    'type': 'object',
                    'data': transform_data
                })
        
        return {
            'success': True,
            'robot_object': robot_object.name,
            'keyframes': keyframes,
            'frame_range': (frame_start, frame_end),
            'fps': scene.render.fps
        }
    
    def _find_robot_object(self) -> Optional[bpy.types.Object]:
        """Find the robot object in the scene."""
        
        # Look for objects with robot-like names
        robot_keywords = ['robot', 'arm', 'manipulator', 'abb', 'kuka', 'fanuc', 'ur']
        
        for obj in bpy.context.scene.objects:
            obj_name = obj.name.lower()
            if any(keyword in obj_name for keyword in robot_keywords):
                if obj.type in ['ARMATURE', 'MESH']:
                    return obj
        
        # Look for armatures (likely to be robots)
        armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
        if armatures:
            return armatures[0]
        
        # Look for selected object
        if bpy.context.active_object and bpy.context.active_object.type in ['ARMATURE', 'MESH']:
            return bpy.context.active_object
        
        return None
    
    def _extract_bone_transformations(self, armature_obj: bpy.types.Object) -> Dict[str, Any]:
        """Extract bone transformations from armature."""
        
        bone_data = {}
        
        if armature_obj.type == 'ARMATURE' and armature_obj.pose:
            for pose_bone in armature_obj.pose.bones:
                # Get bone matrix in world space
                bone_matrix = armature_obj.matrix_world @ pose_bone.matrix
                
                # Extract position, rotation, scale
                location, rotation, scale = bone_matrix.decompose()
                
                bone_data[pose_bone.name] = {
                    'location': list(location),
                    'rotation_euler': list(rotation.to_euler()),
                    'rotation_quaternion': list(rotation),
                    'scale': list(scale),
                    'matrix': [list(row) for row in bone_matrix]
                }
        
        return bone_data
    
    def _extract_object_transformation(self, obj: bpy.types.Object) -> Dict[str, Any]:
        """Extract object transformation."""
        
        matrix = obj.matrix_world
        location, rotation, scale = matrix.decompose()
        
        return {
            'location': list(location),
            'rotation_euler': list(rotation.to_euler()),
            'rotation_quaternion': list(rotation),
            'scale': list(scale),
            'matrix': [list(row) for row in matrix]
        }
    
    def _convert_to_robot_coordinates(self, keyframes: List[Dict[str, Any]], 
                                    robot_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Blender coordinates to robot coordinate system."""
        
        robot_coordinates = []
        coord_transform = self.coordinate_systems['blender_to_robot']
        
        for keyframe in keyframes:
            converted_data = {}
            
            if keyframe['type'] == 'armature':
                # Convert each bone
                for bone_name, bone_data in keyframe['data'].items():
                    converted_data[bone_name] = self._transform_coordinates(
                        bone_data, coord_transform
                    )
            else:
                # Convert object data
                converted_data = self._transform_coordinates(
                    keyframe['data'], coord_transform
                )
            
            robot_coordinates.append({
                'frame': keyframe['frame'],
                'timestamp': keyframe['timestamp'],
                'type': keyframe['type'],
                'data': converted_data
            })
        
        return robot_coordinates
    
    def _transform_coordinates(self, transform_data: Dict[str, Any], 
                             coord_transform: Dict[str, Any]) -> Dict[str, Any]:
        """Transform coordinates using specified transformation."""
        
        # Apply scale factor
        location = Vector(transform_data['location']) * coord_transform['scale_factor']
        
        # Apply rotation transformation
        rotation_matrix = coord_transform['rotation_matrix']
        location = rotation_matrix @ location
        
        # Apply origin offset
        location += coord_transform['origin_offset']
        
        # Transform rotation
        original_rotation = Euler(transform_data['rotation_euler'])
        rotation_matrix_3x3 = rotation_matrix.to_3x3()
        transformed_rotation = rotation_matrix_3x3 @ original_rotation.to_matrix()
        
        return {
            'location': list(location),
            'rotation_euler': list(transformed_rotation.to_euler()),
            'original_data': transform_data
        }
    
    def _generate_motion_path(self, robot_coordinates: List[Dict[str, Any]], 
                            robot_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate motion path with move types and parameters."""
        
        motion_path = []
        
        # Add initial move to safe position
        motion_path.append({
            'move_type': 'joint',
            'position': robot_profile['safe_position'],
            'speed': self.config['max_joint_speed'] * 0.5,  # Slow for safety
            'comment': 'Move to safe position'
        })
        
        # Process keyframes into moves
        for i, keyframe in enumerate(robot_coordinates):
            if keyframe['type'] == 'armature':
                # Use end effector position from kinematic chain
                end_effector_pos = self._calculate_end_effector_position(keyframe['data'])
            else:
                # Use object position
                end_effector_pos = keyframe['data']['location']
            
            # Determine move type
            if i == 0:
                move_type = 'joint'  # First move is always joint move
                speed = self.config['max_joint_speed'] * 0.3
            else:
                # Use linear moves for smooth paths
                move_type = 'linear'
                speed = self._calculate_optimal_speed(motion_path[-1], end_effector_pos)
            
            motion_path.append({
                'move_type': move_type,
                'position': end_effector_pos,
                'orientation': keyframe['data'].get('rotation_euler', [0, 0, 0]),
                'speed': speed,
                'timestamp': keyframe['timestamp'],
                'comment': f'Frame {keyframe["frame"]}'
            })
        
        # Add final move back to safe position
        motion_path.append({
            'move_type': 'joint',
            'position': robot_profile['safe_position'],
            'speed': self.config['max_joint_speed'] * 0.5,
            'comment': 'Return to safe position'
        })
        
        return motion_path
    
    def _calculate_end_effector_position(self, bone_data: Dict[str, Any]) -> List[float]:
        """Calculate end effector position from bone chain."""
        
        # Simple heuristic: use the last bone in alphabetical order
        # In a real implementation, this would use proper forward kinematics
        
        if not bone_data:
            return [0, 0, 0]
        
        # Find end effector bone (often named 'tool', 'end_effector', or last in chain)
        end_effector_candidates = []
        for bone_name, data in bone_data.items():
            if any(keyword in bone_name.lower() for keyword in ['tool', 'end', 'effector', 'tcp']):
                end_effector_candidates.append((bone_name, data))
        
        if end_effector_candidates:
            return end_effector_candidates[0][1]['location']
        
        # Fallback: use the bone with highest Z coordinate
        highest_bone = max(bone_data.items(), key=lambda x: x[1]['location'][2])
        return highest_bone[1]['location']
    
    def _calculate_optimal_speed(self, previous_move: Dict[str, Any], 
                               current_position: List[float]) -> float:
        """Calculate optimal speed for move."""
        
        if 'position' not in previous_move:
            return self.config['max_linear_speed'] * 0.5
        
        # Calculate distance
        prev_pos = Vector(previous_move['position'])
        curr_pos = Vector(current_position)
        distance = (curr_pos - prev_pos).length
        
        # Adjust speed based on distance (slower for short moves)
        if distance < 10:  # mm
            return self.config['max_linear_speed'] * 0.2
        elif distance < 50:
            return self.config['max_linear_speed'] * 0.5
        else:
            return self.config['max_linear_speed'] * 0.8
    
    def _optimize_motion_path(self, motion_path: List[Dict[str, Any]], 
                            robot_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize motion path for efficiency and smoothness."""
        
        if len(motion_path) < 3:
            return motion_path
        
        optimized_path = [motion_path[0]]  # Keep first move
        
        # Remove redundant moves and smooth path
        for i in range(1, len(motion_path) - 1):
            current_move = motion_path[i]
            next_move = motion_path[i + 1]
            
            # Check if moves can be combined
            if self._can_combine_moves(optimized_path[-1], current_move, next_move):
                # Skip current move, it will be combined with next
                continue
            else:
                optimized_path.append(current_move)
        
        optimized_path.append(motion_path[-1])  # Keep last move
        
        return optimized_path
    
    def _can_combine_moves(self, prev_move: Dict[str, Any], 
                          current_move: Dict[str, Any], 
                          next_move: Dict[str, Any]) -> bool:
        """Check if moves can be combined for optimization."""
        
        # Only combine linear moves
        if not all(move['move_type'] == 'linear' for move in [prev_move, current_move, next_move]):
            return False
        
        # Check if moves are collinear within tolerance
        prev_pos = Vector(prev_move['position'])
        curr_pos = Vector(current_move['position'])
        next_pos = Vector(next_move['position'])
        
        # Calculate vectors
        vec1 = curr_pos - prev_pos
        vec2 = next_pos - curr_pos
        
        # Check collinearity (angle between vectors)
        if vec1.length > 0 and vec2.length > 0:
            angle = vec1.angle(vec2)
            return angle < math.radians(5)  # 5 degree tolerance
        
        return False
    
    def _generate_gcode_content(self, motion_path: List[Dict[str, Any]], 
                              robot_profile: Dict[str, Any]) -> str:
        """Generate GCODE content from motion path."""
        
        gcode_lines = []
        
        # Add header
        gcode_lines.extend(self._generate_header(robot_profile))
        
        # Add initialization
        gcode_lines.extend(self._generate_initialization(robot_profile))
        
        # Add motion commands
        for i, move in enumerate(motion_path):
            gcode_lines.extend(self._generate_move_command(move, robot_profile, i))
        
        # Add footer
        gcode_lines.extend(self._generate_footer(robot_profile))
        
        return '\n'.join(gcode_lines)
    
    def _generate_header(self, robot_profile: Dict[str, Any]) -> List[str]:
        """Generate GCODE header."""
        
        header = []
        
        if self.config['include_comments']:
            header.extend([
                f"; Generated by ProcessAnimator for {robot_profile['language']}",
                f"; Robot Type: {robot_profile.get('robot_type', 'Unknown')}",
                f"; Generated at: {bpy.context.scene.frame_current}",
                f"; Units: {self.config['units']}",
                f"; Coordinate System: {robot_profile['coordinate_system']}",
                ";"
            ])
        
        # Language-specific headers
        if robot_profile['language'] == 'RAPID':
            header.extend([
                "MODULE MainModule",
                "CONST robtarget Home := [[0,0,0],[1,0,0,0],[0,0,0,0],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];",
                "PROC main()",
                ""
            ])
        elif robot_profile['language'] == 'KRL':
            header.extend([
                "&ACCESS RVP",
                "&REL 1",
                "DEF ProcessAnimator_Program()",
                "DECL AXIS HOME_POS",
                "DECL POS CURRENT_POS",
                ""
            ])
        elif robot_profile['language'] == 'URScript':
            header.extend([
                "def main():",
                f"  set_tcp(p[{','.join(map(str, robot_profile['tool_offset']))}])",
                ""
            ])
        
        return header
    
    def _generate_initialization(self, robot_profile: Dict[str, Any]) -> List[str]:
        """Generate initialization commands."""
        
        init_commands = []
        
        if self.config['include_comments']:
            init_commands.append("; Initialization")
        
        # Set tool
        tool_cmd = robot_profile['commands'].get('set_tool', '')
        if tool_cmd:
            if robot_profile['language'] == 'RAPID':
                init_commands.append(f"  ConfJ \\Off;")
                init_commands.append(f"  ConfL \\Off;")
            elif robot_profile['language'] == 'URScript':
                init_commands.append(f"  set_tcp(p[{','.join(map(str, robot_profile['tool_offset']))}])")
        
        init_commands.append("")
        return init_commands
    
    def _generate_move_command(self, move: Dict[str, Any], 
                             robot_profile: Dict[str, Any], 
                             move_index: int) -> List[str]:
        """Generate move command for specific robot language."""
        
        commands = []
        
        if self.config['include_comments'] and 'comment' in move:
            commands.append(f"; {move['comment']}")
        
        position = move['position']
        orientation = move.get('orientation', [0, 0, 0])
        speed = move.get('speed', 100)
        
        # Format position with precision
        precision = self.config['coordinate_precision']
        pos_str = ','.join(f"{p:.{precision}f}" for p in position)
        
        if robot_profile['language'] == 'RAPID':
            if move['move_type'] == 'joint':
                commands.append(f"  MoveJ [{pos_str}], v{speed:.0f}, fine, tool0;")
            else:
                commands.append(f"  MoveL [{pos_str}], v{speed:.0f}, z1, tool0;")
        
        elif robot_profile['language'] == 'KRL':
            if move['move_type'] == 'joint':
                commands.append(f"  PTP {{A1 {position[0]:.{precision}f}, A2 {position[1]:.{precision}f}, A3 {position[2]:.{precision}f}, A4 {position[3]:.{precision}f}, A5 {position[4]:.{precision}f}, A6 {position[5]:.{precision}f}}}")
            else:
                commands.append(f"  LIN {{X {position[0]:.{precision}f}, Y {position[1]:.{precision}f}, Z {position[2]:.{precision}f}, A {orientation[0]:.{precision}f}, B {orientation[1]:.{precision}f}, C {orientation[2]:.{precision}f}}}")
        
        elif robot_profile['language'] == 'URScript':
            if move['move_type'] == 'joint':
                commands.append(f"  movej([{pos_str}], a=1.4, v={speed/100:.2f})")
            else:
                commands.append(f"  movel(p[{pos_str}], a=1.2, v={speed/1000:.3f})")
        
        else:  # Generic GCODE
            if move['move_type'] == 'joint':
                commands.append(f"G0 X{position[0]:.{precision}f} Y{position[1]:.{precision}f} Z{position[2]:.{precision}f}")
            else:
                commands.append(f"G1 X{position[0]:.{precision}f} Y{position[1]:.{precision}f} Z{position[2]:.{precision}f} F{speed:.0f}")
        
        return commands
    
    def _generate_footer(self, robot_profile: Dict[str, Any]) -> List[str]:
        """Generate GCODE footer."""
        
        footer = []
        
        if self.config['include_comments']:
            footer.append("; End of program")
        
        # Language-specific footers
        if robot_profile['language'] == 'RAPID':
            footer.extend([
                "ENDPROC",
                "ENDMODULE"
            ])
        elif robot_profile['language'] == 'KRL':
            footer.extend([
                "END"
            ])
        elif robot_profile['language'] == 'URScript':
            footer.extend([
                "end"
            ])
        else:  # Generic GCODE
            footer.extend([
                "M30 ; End program"
            ])
        
        return footer
    
    def _add_safety_checks(self, gcode_content: str, robot_profile: Dict[str, Any]) -> str:
        """Add safety checks to GCODE."""
        
        if not self.config['include_safety_stops']:
            return gcode_content
        
        lines = gcode_content.split('\n')
        safe_lines = []
        
        # Add safety check before each move
        for line in lines:
            safe_lines.append(line)
            
            # Add safety pause after dangerous moves
            if any(cmd in line for cmd in ['MoveJ', 'MoveL', 'movej', 'movel', 'G0', 'G1']):
                if self.config['include_comments']:
                    safe_lines.append("; Safety check")
                
                if robot_profile['language'] == 'RAPID':
                    safe_lines.append("  WaitTime 0.1;")
                elif robot_profile['language'] == 'URScript':
                    safe_lines.append("  sleep(0.1)")
                elif robot_profile['language'] == 'GCODE':
                    safe_lines.append("G4 P100")
        
        return '\n'.join(safe_lines)
    
    def _write_gcode_file(self, gcode_content: str, output_path: str, 
                         robot_profile: Dict[str, Any]) -> str:
        """Write GCODE content to file."""
        
        # Ensure correct file extension
        file_extension = robot_profile['file_extension']
        if not output_path.endswith(file_extension):
            output_path = os.path.splitext(output_path)[0] + file_extension
        
        # Expand Blender path prefix
        if output_path.startswith('//'):
            output_path = bpy.path.abspath(output_path)
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(gcode_content)
        
        return output_path
    
    def _estimate_execution_time(self, motion_path: List[Dict[str, Any]]) -> float:
        """Estimate execution time for motion path."""
        
        total_time = 0.0
        
        for move in motion_path:
            if 'timestamp' in move and len(motion_path) > 1:
                # Use animation timing
                total_time = max(total_time, move['timestamp'])
            else:
                # Estimate based on distance and speed
                if 'position' in move:
                    distance = Vector(move['position']).length
                    speed = move.get('speed', 100)
                    total_time += distance / speed * 60  # Convert to seconds
        
        return total_time
    
    def validate_gcode(self, gcode_content: str, robot_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated GCODE for safety and correctness."""
        
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
        
        lines = gcode_content.split('\n')
        
        # Count different move types
        move_counts = {'joint': 0, 'linear': 0, 'circular': 0}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # Check for valid commands
            if robot_profile['language'] == 'RAPID':
                if 'MoveJ' in line:
                    move_counts['joint'] += 1
                elif 'MoveL' in line:
                    move_counts['linear'] += 1
                elif 'MoveC' in line:
                    move_counts['circular'] += 1
            
            # Check for safety issues
            if 'speed' in line.lower() and robot_profile['language'] == 'RAPID':
                # Extract speed value and check limits
                speed_match = line.split('v')[1].split(',')[0] if 'v' in line else '0'
                try:
                    speed_val = float(speed_match)
                    if speed_val > self.config['max_linear_speed']:
                        validation_result['warnings'].append(f"High speed detected: {speed_val}")
                except ValueError:
                    pass
        
        validation_result['statistics'] = move_counts
        
        return validation_result 