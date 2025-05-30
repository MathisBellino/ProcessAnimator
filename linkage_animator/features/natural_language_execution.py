#!/usr/bin/env python3
"""
Natural Language Robot Execution System

Interprets natural language commands and executes robot motions automatically.
Example: "pick up the tube and place it on the table" → automatic execution
"""

import bpy
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from mathutils import Vector
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty
import logging

logger = logging.getLogger(__name__)


class NaturalLanguageExecutor:
    """
    Natural language command interpreter and executor for robot actions.
    """
    
    def __init__(self):
        self.command_patterns = self._load_command_patterns()
        self.object_database = {}
        self.execution_queue = []
        self.current_robot = None
        
        logger.info("Natural Language Executor initialized")
    
    def _load_command_patterns(self) -> Dict[str, Any]:
        """Load command patterns for natural language interpretation."""
        return {
            'pick_and_place': {
                'patterns': [
                    r'pick up (?:the )?(.+?) and (?:place|put) (?:it )?(?:on|in|at) (?:the )?(.+)',
                    r'move (?:the )?(.+?) (?:to|onto) (?:the )?(.+)',
                    r'take (?:the )?(.+?) and (?:place|put) (?:it )?(?:on|in) (?:the )?(.+)',
                    r'grab (?:the )?(.+?) and (?:move|transfer) (?:it )?(?:to|onto) (?:the )?(.+)'
                ],
                'action_type': 'pick_and_place',
                'parameters': ['source_object', 'target_location']
            },
            'simple_pick': {
                'patterns': [
                    r'pick up (?:the )?(.+)',
                    r'grab (?:the )?(.+)',
                    r'take (?:the )?(.+)'
                ],
                'action_type': 'pick',
                'parameters': ['target_object']
            },
            'simple_place': {
                'patterns': [
                    r'place (?:it )?(?:on|in|at) (?:the )?(.+)',
                    r'put (?:it )?(?:on|in|at) (?:the )?(.+)',
                    r'set (?:it )?(?:down )?(?:on|at) (?:the )?(.+)'
                ],
                'action_type': 'place',
                'parameters': ['target_location']
            },
            'movement': {
                'patterns': [
                    r'move (?:to|towards) (?:the )?(.+)',
                    r'go to (?:the )?(.+)',
                    r'approach (?:the )?(.+)'
                ],
                'action_type': 'move',
                'parameters': ['target_location']
            },
            'multi_step': {
                'patterns': [
                    r'(.+), then (.+)',
                    r'first (.+), then (.+)',
                    r'(.+) and then (.+)'
                ],
                'action_type': 'sequence',
                'parameters': ['first_action', 'second_action']
            }
        }
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """Parse natural language command into actionable parameters."""
        command = command.lower().strip()
        
        # Try to match against known patterns
        for command_type, config in self.command_patterns.items():
            for pattern in config['patterns']:
                match = re.search(pattern, command)
                if match:
                    return {
                        'success': True,
                        'command_type': command_type,
                        'action_type': config['action_type'],
                        'parameters': dict(zip(config['parameters'], match.groups())),
                        'raw_command': command,
                        'confidence': 0.9  # High confidence for pattern match
                    }
        
        # Fallback: try to extract objects and actions
        fallback_result = self._fallback_parsing(command)
        return fallback_result
    
    def _fallback_parsing(self, command: str) -> Dict[str, Any]:
        """Fallback parsing for commands that don't match patterns."""
        # Extract common action words
        action_words = {
            'pick': ['pick', 'grab', 'take', 'lift'],
            'place': ['place', 'put', 'set', 'drop'],
            'move': ['move', 'go', 'approach', 'navigate']
        }
        
        detected_actions = []
        for action, keywords in action_words.items():
            if any(keyword in command for keyword in keywords):
                detected_actions.append(action)
        
        # Extract object references
        object_refs = self._extract_object_references(command)
        
        if detected_actions and object_refs:
            return {
                'success': True,
                'command_type': 'parsed',
                'action_type': detected_actions[0],  # Use first detected action
                'parameters': {
                    'objects': object_refs,
                    'actions': detected_actions
                },
                'raw_command': command,
                'confidence': 0.6  # Lower confidence for fallback
            }
        
        return {
            'success': False,
            'error': 'Could not parse command',
            'raw_command': command,
            'confidence': 0.0
        }
    
    def _extract_object_references(self, command: str) -> List[str]:
        """Extract object references from command text."""
        # Common object names and their variants
        object_patterns = [
            r'\b(tube|cylinder|pipe)\b',
            r'\b(box|cube|container)\b',
            r'\b(table|desk|surface)\b',
            r'\b(ball|sphere|orb)\b',
            r'\b(cup|glass|mug)\b',
            r'\b(part|component|piece)\b',
            r'\b(screw|bolt|fastener)\b',
            r'\b(tool|instrument)\b'
        ]
        
        found_objects = []
        for pattern in object_patterns:
            matches = re.finditer(pattern, command)
            for match in matches:
                found_objects.append(match.group(1))
        
        return found_objects
    
    def execute_command(self, command: str, context) -> Dict[str, Any]:
        """Execute a natural language command."""
        # Parse the command
        parsed = self.parse_command(command)
        
        if not parsed['success']:
            return parsed
        
        # Find robot in scene
        robot = self._find_robot_in_scene(context)
        if not robot:
            return {
                'success': False,
                'error': 'No robot found in scene. Please import a robot first.',
                'parsed_command': parsed
            }
        
        self.current_robot = robot
        
        # Build object database
        self._build_object_database(context)
        
        # Execute based on action type
        action_type = parsed['action_type']
        
        if action_type == 'pick_and_place':
            return self._execute_pick_and_place(parsed, context)
        elif action_type == 'pick':
            return self._execute_pick(parsed, context)
        elif action_type == 'place':
            return self._execute_place(parsed, context)
        elif action_type == 'move':
            return self._execute_move(parsed, context)
        elif action_type == 'sequence':
            return self._execute_sequence(parsed, context)
        else:
            return {
                'success': False,
                'error': f'Action type "{action_type}" not implemented',
                'parsed_command': parsed
            }
    
    def _find_robot_in_scene(self, context) -> Optional[bpy.types.Object]:
        """Find robot armature in the scene."""
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                # Check if it has robot properties
                if obj.get('robot_id') or obj.get('robot_name') or 'robot' in obj.name.lower():
                    return obj
            
        # Fallback: return first armature
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                return obj
        
        return None
    
    def _build_object_database(self, context):
        """Build database of objects in the scene for reference."""
        self.object_database = {}
        
        for obj in context.scene.objects:
            if obj.type == 'MESH' and not obj.name.startswith('Robot_'):
                # Categorize objects by name patterns
                name_lower = obj.name.lower()
                
                categories = []
                if any(word in name_lower for word in ['tube', 'cylinder', 'pipe']):
                    categories.append('tube')
                if any(word in name_lower for word in ['box', 'cube', 'container']):
                    categories.append('box')
                if any(word in name_lower for word in ['table', 'desk', 'surface', 'plane']):
                    categories.append('table')
                if any(word in name_lower for word in ['part', 'component']):
                    categories.append('part')
                
                # Store object with its categories
                self.object_database[obj.name] = {
                    'object': obj,
                    'categories': categories,
                    'location': obj.location.copy(),
                    'size': self._calculate_object_size(obj)
                }
    
    def _calculate_object_size(self, obj) -> float:
        """Calculate approximate size of object."""
        if obj.type == 'MESH' and obj.data.vertices:
            # Calculate bounding box diagonal
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            min_coord = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
            max_coord = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
            return (max_coord - min_coord).length
        return 1.0
    
    def _find_object_by_name(self, object_name: str) -> Optional[bpy.types.Object]:
        """Find object in scene by name or category."""
        object_name = object_name.lower().strip()
        
        # Direct name match
        for obj_name, obj_data in self.object_database.items():
            if object_name in obj_name.lower():
                return obj_data['object']
        
        # Category match
        for obj_name, obj_data in self.object_database.items():
            if object_name in obj_data['categories']:
                return obj_data['object']
        
        return None
    
    def _execute_pick_and_place(self, parsed: Dict, context) -> Dict[str, Any]:
        """Execute pick and place action."""
        params = parsed['parameters']
        source_obj = self._find_object_by_name(params['source_object'])
        target_location = self._find_object_by_name(params['target_location'])
        
        if not source_obj:
            return {
                'success': False,
                'error': f'Could not find object: {params["source_object"]}',
                'parsed_command': parsed
            }
        
        if not target_location:
            return {
                'success': False,
                'error': f'Could not find target location: {params["target_location"]}',
                'parsed_command': parsed
            }
        
        # Execute the motion
        result = self._create_pick_and_place_animation(source_obj, target_location, context)
        
        return {
            'success': result['success'],
            'message': f'Executing: Pick up {source_obj.name} and place on {target_location.name}',
            'source_object': source_obj.name,
            'target_location': target_location.name,
            'animation_result': result,
            'parsed_command': parsed
        }
    
    def _execute_pick(self, parsed: Dict, context) -> Dict[str, Any]:
        """Execute simple pick action."""
        params = parsed['parameters']
        target_obj = self._find_object_by_name(params['target_object'])
        
        if not target_obj:
            return {
                'success': False,
                'error': f'Could not find object: {params["target_object"]}',
                'parsed_command': parsed
            }
        
        result = self._create_pick_animation(target_obj, context)
        
        return {
            'success': result['success'],
            'message': f'Executing: Pick up {target_obj.name}',
            'target_object': target_obj.name,
            'animation_result': result,
            'parsed_command': parsed
        }
    
    def _execute_place(self, parsed: Dict, context) -> Dict[str, Any]:
        """Execute simple place action."""
        params = parsed['parameters']
        target_location = self._find_object_by_name(params['target_location'])
        
        if not target_location:
            return {
                'success': False,
                'error': f'Could not find target location: {params["target_location"]}',
                'parsed_command': parsed
            }
        
        result = self._create_place_animation(target_location, context)
        
        return {
            'success': result['success'],
            'message': f'Executing: Place on {target_location.name}',
            'target_location': target_location.name,
            'animation_result': result,
            'parsed_command': parsed
        }
    
    def _execute_move(self, parsed: Dict, context) -> Dict[str, Any]:
        """Execute simple move action."""
        params = parsed['parameters']
        target_location = self._find_object_by_name(params['target_location'])
        
        if not target_location:
            return {
                'success': False,
                'error': f'Could not find target location: {params["target_location"]}',
                'parsed_command': parsed
            }
        
        result = self._create_move_animation(target_location, context)
        
        return {
            'success': result['success'],
            'message': f'Executing: Move to {target_location.name}',
            'target_location': target_location.name,
            'animation_result': result,
            'parsed_command': parsed
        }
    
    def _execute_sequence(self, parsed: Dict, context) -> Dict[str, Any]:
        """Execute sequence of actions."""
        params = parsed['parameters']
        
        # Parse sub-commands
        first_result = self.execute_command(params['first_action'], context)
        if not first_result['success']:
            return first_result
        
        second_result = self.execute_command(params['second_action'], context)
        
        return {
            'success': second_result['success'],
            'message': f'Executing sequence: {params["first_action"]} → {params["second_action"]}',
            'first_action_result': first_result,
            'second_action_result': second_result,
            'parsed_command': parsed
        }
    
    def _create_pick_and_place_animation(self, source_obj, target_obj, context) -> Dict[str, Any]:
        """Create actual pick and place animation."""
        if not self.current_robot:
            return {'success': False, 'error': 'No robot available'}
        
        try:
            # Get robot end effector (assume last bone or specific bone)
            end_effector = self._get_robot_end_effector()
            if not end_effector:
                return {'success': False, 'error': 'Could not find robot end effector'}
            
            # Calculate keyframes
            keyframes = self._calculate_pick_and_place_keyframes(source_obj, target_obj)
            
            # Apply animation
            self._apply_keyframes_to_robot(end_effector, keyframes, context)
            
            return {
                'success': True,
                'keyframes': len(keyframes),
                'duration': len(keyframes) / 24.0  # Assume 24 fps
            }
            
        except Exception as e:
            logger.error(f"Animation creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_pick_animation(self, target_obj, context) -> Dict[str, Any]:
        """Create pick-only animation."""
        try:
            end_effector = self._get_robot_end_effector()
            if not end_effector:
                return {'success': False, 'error': 'Could not find robot end effector'}
            
            keyframes = self._calculate_pick_keyframes(target_obj)
            self._apply_keyframes_to_robot(end_effector, keyframes, context)
            
            return {'success': True, 'keyframes': len(keyframes)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_place_animation(self, target_obj, context) -> Dict[str, Any]:
        """Create place-only animation."""
        try:
            end_effector = self._get_robot_end_effector()
            if not end_effector:
                return {'success': False, 'error': 'Could not find robot end effector'}
            
            keyframes = self._calculate_place_keyframes(target_obj)
            self._apply_keyframes_to_robot(end_effector, keyframes, context)
            
            return {'success': True, 'keyframes': len(keyframes)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_move_animation(self, target_obj, context) -> Dict[str, Any]:
        """Create move-only animation."""
        try:
            end_effector = self._get_robot_end_effector()
            if not end_effector:
                return {'success': False, 'error': 'Could not find robot end effector'}
            
            keyframes = self._calculate_move_keyframes(target_obj)
            self._apply_keyframes_to_robot(end_effector, keyframes, context)
            
            return {'success': True, 'keyframes': len(keyframes)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_robot_end_effector(self):
        """Get robot end effector bone."""
        if not self.current_robot or self.current_robot.type != 'ARMATURE':
            return None
        
        # Look for common end effector names
        end_effector_names = ['end_effector', 'gripper', 'hand', 'tool', 'tcp']
        
        for bone in self.current_robot.pose.bones:
            bone_name_lower = bone.name.lower()
            if any(name in bone_name_lower for name in end_effector_names):
                return bone
        
        # Fallback: use last bone (leaf bone)
        if self.current_robot.pose.bones:
            # Find bone with no children
            for bone in self.current_robot.pose.bones:
                if not bone.children:
                    return bone
        
        return None
    
    def _calculate_pick_and_place_keyframes(self, source_obj, target_obj) -> List[Dict]:
        """Calculate keyframes for pick and place motion."""
        keyframes = []
        
        # Start position (current robot position)
        start_pos = self.current_robot.location.copy()
        
        # Approach source object
        approach_pos = source_obj.location.copy()
        approach_pos.z += 0.5  # Approach from above
        
        # Pick position
        pick_pos = source_obj.location.copy()
        pick_pos.z += 0.1  # Just above object
        
        # Lift position
        lift_pos = pick_pos.copy()
        lift_pos.z += 0.3
        
        # Approach target
        target_approach = target_obj.location.copy()
        target_approach.z += 0.5
        
        # Place position
        place_pos = target_obj.location.copy()
        place_pos.z += 0.2  # Place above target
        
        # Create keyframe sequence
        frame = 1
        frame_step = 24  # 1 second per step at 24fps
        
        keyframes = [
            {'frame': frame, 'location': start_pos, 'action': 'start'},
            {'frame': frame + frame_step, 'location': approach_pos, 'action': 'approach_source'},
            {'frame': frame + frame_step * 2, 'location': pick_pos, 'action': 'pick'},
            {'frame': frame + frame_step * 3, 'location': lift_pos, 'action': 'lift'},
            {'frame': frame + frame_step * 4, 'location': target_approach, 'action': 'approach_target'},
            {'frame': frame + frame_step * 5, 'location': place_pos, 'action': 'place'},
        ]
        
        return keyframes
    
    def _calculate_pick_keyframes(self, target_obj) -> List[Dict]:
        """Calculate keyframes for pick-only motion."""
        start_pos = self.current_robot.location.copy()
        approach_pos = target_obj.location.copy()
        approach_pos.z += 0.5
        pick_pos = target_obj.location.copy()
        pick_pos.z += 0.1
        
        return [
            {'frame': 1, 'location': start_pos, 'action': 'start'},
            {'frame': 25, 'location': approach_pos, 'action': 'approach'},
            {'frame': 49, 'location': pick_pos, 'action': 'pick'},
        ]
    
    def _calculate_place_keyframes(self, target_obj) -> List[Dict]:
        """Calculate keyframes for place-only motion."""
        start_pos = self.current_robot.location.copy()
        approach_pos = target_obj.location.copy()
        approach_pos.z += 0.5
        place_pos = target_obj.location.copy()
        place_pos.z += 0.2
        
        return [
            {'frame': 1, 'location': start_pos, 'action': 'start'},
            {'frame': 25, 'location': approach_pos, 'action': 'approach'},
            {'frame': 49, 'location': place_pos, 'action': 'place'},
        ]
    
    def _calculate_move_keyframes(self, target_obj) -> List[Dict]:
        """Calculate keyframes for move-only motion."""
        start_pos = self.current_robot.location.copy()
        target_pos = target_obj.location.copy()
        target_pos.z += 0.3  # Move above target
        
        return [
            {'frame': 1, 'location': start_pos, 'action': 'start'},
            {'frame': 49, 'location': target_pos, 'action': 'arrive'},
        ]
    
    def _apply_keyframes_to_robot(self, end_effector, keyframes, context):
        """Apply calculated keyframes to robot."""
        if not end_effector:
            return
        
        # Switch to pose mode
        bpy.context.view_layer.objects.active = self.current_robot
        bpy.ops.object.mode_set(mode='POSE')
        
        # Clear existing keyframes
        if end_effector.location:
            end_effector.location = (0, 0, 0)
        
        # Apply keyframes
        for keyframe in keyframes:
            context.scene.frame_set(keyframe['frame'])
            
            # Calculate relative position
            relative_pos = keyframe['location'] - self.current_robot.location
            end_effector.location = relative_pos
            
            # Insert keyframe
            end_effector.keyframe_insert(data_path="location", frame=keyframe['frame'])
        
        # Set frame range
        context.scene.frame_start = 1
        context.scene.frame_end = max(kf['frame'] for kf in keyframes)
        context.scene.frame_current = 1
        
        logger.info(f"Applied {len(keyframes)} keyframes to robot")


class ROBOTANIM_OT_execute_natural_language(Operator):
    """Execute natural language robot command"""
    bl_idname = "robotanim.execute_natural_language"
    bl_label = "Execute Command"
    bl_description = "Execute natural language robot command"
    bl_options = {'REGISTER', 'UNDO'}
    
    command: StringProperty(
        name="Command",
        description="Natural language command to execute",
        default=""
    )
    
    def execute(self, context):
        if not self.command.strip():
            self.report({'ERROR'}, "Please enter a command")
            return {'CANCELLED'}
        
        # Get or create executor
        if not hasattr(bpy.types.Scene, '_nl_executor'):
            bpy.types.Scene._nl_executor = NaturalLanguageExecutor()
        
        executor = bpy.types.Scene._nl_executor
        
        # Execute command
        result = executor.execute_command(self.command, context)
        
        if result['success']:
            self.report({'INFO'}, result['message'])
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result['error'])
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "command")


class ROBOTANIM_PT_natural_language(Panel):
    """Panel for natural language commands"""
    bl_label = "🗣️ Natural Language Control"
    bl_idname = "ROBOTANIM_PT_natural_language"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    def draw(self, context):
        layout = self.layout
        
        # Command examples
        examples_box = layout.box()
        examples_box.label(text="📝 Example Commands:", icon='INFO')
        examples_box.label(text='• "Pick up the tube and place it on the table"')
        examples_box.label(text='• "Move the box to the assembly station"')
        examples_box.label(text='• "Grab the part and put it in the container"')
        
        layout.separator()
        
        # Quick command buttons
        quick_box = layout.box()
        quick_box.label(text="⚡ Quick Commands:", icon='PLAY')
        
        # Pre-defined commands
        quick_commands = [
            ("Pick up tube", "pick up the tube"),
            ("Place on table", "place it on the table"),
            ("Move to assembly", "move to the assembly station")
        ]
        
        for label, command in quick_commands:
            op = quick_box.operator("robotanim.execute_natural_language", text=label)
            op.command = command
        
        layout.separator()
        
        # Custom command input
        custom_box = layout.box()
        custom_box.label(text="✏️ Custom Command:", icon='CONSOLE')
        custom_box.operator("robotanim.execute_natural_language", 
                           text="Enter Custom Command", 
                           icon='CONSOLE')


# Registration
natural_language_classes = [
    ROBOTANIM_OT_execute_natural_language,
    ROBOTANIM_PT_natural_language,
]


def register_natural_language():
    """Register natural language classes."""
    for cls in natural_language_classes:
        bpy.utils.register_class(cls)


def unregister_natural_language():
    """Unregister natural language classes."""
    # Clean up executor
    if hasattr(bpy.types.Scene, '_nl_executor'):
        delattr(bpy.types.Scene, '_nl_executor')
    
    # Unregister classes
    for cls in reversed(natural_language_classes):
        bpy.utils.unregister_class(cls) 