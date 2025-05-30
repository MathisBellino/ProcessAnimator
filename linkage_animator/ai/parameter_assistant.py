#!/usr/bin/env python3
"""
AI Parameter Assistant

Conversational AI system that guides users through robot animation setup
by asking intelligent questions and configuring parameters based on responses.
"""

import bpy
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
import logging

logger = logging.getLogger(__name__)


class ParameterAssistantProperties(PropertyGroup):
    """Properties for AI Parameter Assistant."""
    
    current_question: StringProperty(
        name="Current Question",
        description="Current question from AI assistant",
        default=""
    )
    
    user_response: StringProperty(
        name="User Response",
        description="User's response to current question",
        default=""
    )
    
    conversation_active: BoolProperty(
        name="Conversation Active",
        description="Whether AI conversation is currently active",
        default=False
    )
    
    setup_phase: StringProperty(
        name="Setup Phase",
        description="Current phase of parameter setup",
        default="welcome"
    )
    
    confidence_level: FloatProperty(
        name="Confidence Level",
        description="AI confidence in parameter understanding",
        default=0.0,
        min=0.0,
        max=1.0
    )


class AIParameterAssistant:
    """
    AI-powered conversational assistant for robot animation parameter setup.
    
    Uses natural language processing to understand user needs and configure
    animation parameters through guided conversation.
    """
    
    def __init__(self):
        self.conversation_history = []
        self.extracted_parameters = {}
        self.current_phase = "welcome"
        self.guided_suggestions = []
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        self.question_templates = self._load_question_templates()
        
        logger.info("AI Parameter Assistant initialized")
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base for parameter understanding."""
        return {
            'robot_capabilities': {
                'ur5e': {
                    'max_speed': 180,  # deg/s
                    'max_payload': 5.0,  # kg
                    'precision': 0.1,  # mm
                    'typical_applications': ['assembly', 'pick_and_place', 'inspection']
                },
                'kuka_kr10': {
                    'max_speed': 150,
                    'max_payload': 10.0,
                    'precision': 0.05,
                    'typical_applications': ['welding', 'material_handling', 'machining']
                },
                'abb_irb120': {
                    'max_speed': 250,
                    'max_payload': 3.0,
                    'precision': 0.01,
                    'typical_applications': ['electronics', 'small_parts', 'testing']
                }
            },
            'common_tasks': {
                'pick_and_place': {
                    'keywords': ['pick', 'place', 'move', 'transfer', 'grab'],
                    'typical_speed': 'medium',
                    'precision_required': 'medium',
                    'safety_considerations': ['collision_avoidance', 'gentle_grip']
                },
                'welding': {
                    'keywords': ['weld', 'join', 'torch', 'arc', 'seam'],
                    'typical_speed': 'slow',
                    'precision_required': 'high',
                    'safety_considerations': ['heat_protection', 'gas_safety']
                },
                'assembly': {
                    'keywords': ['assemble', 'install', 'connect', 'screw', 'fit'],
                    'typical_speed': 'slow',
                    'precision_required': 'high',
                    'safety_considerations': ['part_alignment', 'force_control']
                }
            },
            'motion_types': {
                'linear': {
                    'keywords': ['straight', 'direct', 'line'],
                    'characteristics': ['simple', 'fast', 'predictable']
                },
                'curved': {
                    'keywords': ['smooth', 'arc', 'curved', 'flowing'],
                    'characteristics': ['natural', 'gentle', 'continuous']
                },
                'precise': {
                    'keywords': ['careful', 'exact', 'precise', 'accurate'],
                    'characteristics': ['slow', 'controlled', 'repeatable']
                }
            }
        }
    
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different conversation phases."""
        return {
            'welcome': [
                "👋 Hi! I'm your AI robot animation assistant. What would you like your robot to do?",
                "🤖 Welcome! Tell me about the task you want to animate - I'll help set everything up perfectly!",
                "✨ Ready to create amazing robot animations? Describe what you have in mind!"
            ],
            'task_clarification': [
                "🎯 That sounds interesting! Can you tell me more about {specific_aspect}?",
                "🔍 I want to make sure I understand - when you say '{user_term}', do you mean {interpretation}?",
                "📝 Got it! A few quick questions to optimize this: {follow_up_question}"
            ],
            'robot_selection': [
                "🤖 Based on your task, I'd recommend the {robot_name}. Does that work for you?",
                "⚙️ For {task_type}, you'll need a robot that can {requirement}. Which robot are you using?",
                "🎯 I have a few robot options that would be perfect for this. Want me to show you?"
            ],
            'parameter_refinement': [
                "⚡ How fast should this happen? Quick and efficient, or slow and precise?",
                "📏 What level of precision do you need? Rough positioning or exact placement?",
                "🛡️ Any safety concerns I should know about? Fragile parts, obstacles, etc.?",
                "🎬 Should I add any special visual effects to make the animation more engaging?"
            ],
            'confirmation': [
                "✅ Perfect! I've configured everything. Ready to build your animation?",
                "🎉 All set! Your parameters look great. Shall we create the scene?",
                "🚀 Everything's optimized for your task. Ready to see the magic happen?"
            ]
        }
    
    def start_conversation(self, context) -> str:
        """Start a new conversation with the user."""
        self.conversation_history = []
        self.extracted_parameters = {}
        self.current_phase = "welcome"
        
        # Set context properties
        context.scene.ai_assistant.conversation_active = True
        context.scene.ai_assistant.setup_phase = "welcome"
        context.scene.ai_assistant.confidence_level = 0.0
        
        # Generate welcome message
        welcome_questions = self.question_templates['welcome']
        question = welcome_questions[0]  # Use first welcome message
        
        context.scene.ai_assistant.current_question = question
        return question
    
    def process_user_response(self, user_input: str, context) -> Dict[str, Any]:
        """
        Process user response and generate next question or action.
        
        Args:
            user_input: User's text response
            context: Blender context
            
        Returns:
            Dictionary containing next question and extracted parameters
        """
        # Add to conversation history
        self.conversation_history.append({
            'phase': self.current_phase,
            'user_input': user_input,
            'timestamp': bpy.app.timers.time_global()
        })
        
        # Extract information from user input
        extracted_info = self._extract_information(user_input)
        self.extracted_parameters.update(extracted_info)
        
        # Update confidence level
        confidence = self._calculate_confidence()
        context.scene.ai_assistant.confidence_level = confidence
        
        # Determine next phase and question
        next_phase, next_question = self._determine_next_question(context)
        
        # Update context
        context.scene.ai_assistant.setup_phase = next_phase
        context.scene.ai_assistant.current_question = next_question
        
        return {
            'question': next_question,
            'parameters': self.extracted_parameters.copy(),
            'confidence': confidence,
            'phase': next_phase,
            'suggestions': self.guided_suggestions.copy()
        }
    
    def _extract_information(self, user_input: str) -> Dict[str, Any]:
        """Extract parameters and information from user input."""
        extracted = {}
        user_lower = user_input.lower()
        
        # Extract task type
        for task, info in self.knowledge_base['common_tasks'].items():
            for keyword in info['keywords']:
                if keyword in user_lower:
                    extracted['task_type'] = task
                    extracted['task_keywords'] = info['keywords']
                    break
        
        # Extract motion preferences
        for motion_type, info in self.knowledge_base['motion_types'].items():
            for keyword in info['keywords']:
                if keyword in user_lower:
                    extracted['motion_preference'] = motion_type
                    break
        
        # Extract speed preferences
        speed_keywords = {
            'fast': ['fast', 'quick', 'rapid', 'speed', 'hurry'],
            'slow': ['slow', 'careful', 'gentle', 'precise'],
            'medium': ['normal', 'moderate', 'standard', 'regular']
        }
        
        for speed, keywords in speed_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                extracted['speed_preference'] = speed
                break
        
        # Extract object information
        object_patterns = [
            r'pick up (\w+)',
            r'move (\w+)',
            r'grab (\w+)',
            r'handle (\w+)',
            r'(\w+) parts?',
            r'work with (\w+)'
        ]
        
        for pattern in object_patterns:
            match = re.search(pattern, user_lower)
            if match:
                extracted['target_object'] = match.group(1)
                break
        
        # Extract coordinate/position information
        position_patterns = [
            r'to (\w+)',
            r'from (\w+) to (\w+)',
            r'position (\w+)',
            r'coordinates? (.+)',
            r'location (.+)'
        ]
        
        for pattern in position_patterns:
            match = re.search(pattern, user_lower)
            if match:
                extracted['position_info'] = match.groups()
                break
        
        # Extract quantity information
        quantity_patterns = [
            r'(\d+) times?',
            r'(\d+) cycles?',
            r'(\d+) repetitions?',
            r'repeat (\d+)',
        ]
        
        for pattern in quantity_patterns:
            match = re.search(pattern, user_lower)
            if match:
                extracted['quantity'] = int(match.group(1))
                break
        
        return extracted
    
    def _calculate_confidence(self) -> float:
        """Calculate AI confidence level based on extracted parameters."""
        required_params = ['task_type', 'motion_preference', 'speed_preference']
        optional_params = ['target_object', 'position_info', 'quantity']
        
        required_score = sum(1 for param in required_params if param in self.extracted_parameters)
        optional_score = sum(0.5 for param in optional_params if param in self.extracted_parameters)
        
        total_possible = len(required_params) + len(optional_params) * 0.5
        confidence = (required_score + optional_score) / total_possible
        
        return min(confidence, 1.0)
    
    def _determine_next_question(self, context) -> Tuple[str, str]:
        """Determine the next question to ask based on current state."""
        confidence = context.scene.ai_assistant.confidence_level
        
        # If confidence is high enough, move to confirmation
        if confidence >= 0.8:
            return self._generate_confirmation_phase()
        
        # Determine what information is missing
        missing_info = self._identify_missing_information()
        
        if 'task_type' not in self.extracted_parameters:
            return 'task_clarification', self._generate_task_clarification_question()
        
        elif 'robot_selection' not in self.extracted_parameters:
            return 'robot_selection', self._generate_robot_selection_question()
        
        elif missing_info:
            return 'parameter_refinement', self._generate_parameter_question(missing_info[0])
        
        else:
            return self._generate_confirmation_phase()
    
    def _identify_missing_information(self) -> List[str]:
        """Identify what information is still needed."""
        missing = []
        
        if 'speed_preference' not in self.extracted_parameters:
            missing.append('speed')
        
        if 'motion_preference' not in self.extracted_parameters:
            missing.append('motion_type')
        
        if 'target_object' not in self.extracted_parameters:
            missing.append('object')
        
        if 'position_info' not in self.extracted_parameters:
            missing.append('positions')
        
        return missing
    
    def _generate_task_clarification_question(self) -> str:
        """Generate a question to clarify the task."""
        questions = [
            "🎯 I'd love to help! Can you describe what specific task you want the robot to perform?",
            "🤖 What should the robot do? For example: pick and place objects, weld parts, assemble components?",
            "✨ Tell me about the main action - what's the robot's job in this animation?"
        ]
        return questions[len(self.conversation_history) % len(questions)]
    
    def _generate_robot_selection_question(self) -> str:
        """Generate a question about robot selection."""
        if 'task_type' in self.extracted_parameters:
            task = self.extracted_parameters['task_type']
            
            # Recommend robot based on task
            robot_recommendations = {
                'pick_and_place': ('UR5e', 'collaborative robot with excellent precision'),
                'welding': ('KUKA KR10', 'industrial robot perfect for welding'),
                'assembly': ('ABB IRB 120', 'compact robot ideal for assembly work')
            }
            
            if task in robot_recommendations:
                robot_name, description = robot_recommendations[task]
                return f"🤖 For {task} tasks, I'd recommend the {robot_name} - it's a {description}. Does that work for you?"
        
        return "🤖 Which robot would you like to use? I can show you options that are perfect for your task!"
    
    def _generate_parameter_question(self, missing_info: str) -> str:
        """Generate a question for missing parameter information."""
        questions = {
            'speed': "⚡ How fast should the robot move? Quick and efficient, or slow and precise?",
            'motion_type': "🎭 What kind of motion do you prefer? Straight lines, smooth curves, or careful precise movements?",
            'object': "📦 What objects will the robot be working with? This helps me set up the right grip and handling.",
            'positions': "📍 Where should the robot start and end? You can describe positions or coordinates."
        }
        
        return questions.get(missing_info, "🤔 Can you tell me a bit more about your requirements?")
    
    def _generate_confirmation_phase(self) -> Tuple[str, str]:
        """Generate confirmation phase question and summary."""
        # Create parameter summary
        summary = self._create_parameter_summary()
        
        question = f"✅ Perfect! Here's what I've configured:\n\n{summary}\n\nReady to build your animation?"
        
        return 'confirmation', question
    
    def _create_parameter_summary(self) -> str:
        """Create a human-readable summary of extracted parameters."""
        summary_parts = []
        
        if 'task_type' in self.extracted_parameters:
            task = self.extracted_parameters['task_type'].replace('_', ' ').title()
            summary_parts.append(f"🎯 Task: {task}")
        
        if 'speed_preference' in self.extracted_parameters:
            speed = self.extracted_parameters['speed_preference'].title()
            summary_parts.append(f"⚡ Speed: {speed}")
        
        if 'motion_preference' in self.extracted_parameters:
            motion = self.extracted_parameters['motion_preference'].title()
            summary_parts.append(f"🎭 Motion: {motion} movements")
        
        if 'target_object' in self.extracted_parameters:
            obj = self.extracted_parameters['target_object'].title()
            summary_parts.append(f"📦 Object: {obj}")
        
        if 'quantity' in self.extracted_parameters:
            qty = self.extracted_parameters['quantity']
            summary_parts.append(f"🔄 Repetitions: {qty}")
        
        return '\n'.join(summary_parts) if summary_parts else "Basic robot animation setup"
    
    def generate_guided_suggestions(self, current_text: str) -> List[str]:
        """Generate contextual suggestions based on current input."""
        suggestions = []
        text_lower = current_text.lower()
        
        # Task-based suggestions
        if not self.extracted_parameters.get('task_type'):
            if any(word in text_lower for word in ['pick', 'grab', 'move']):
                suggestions.extend([
                    "pick up small parts",
                    "move objects to assembly line",
                    "grab and place components"
                ])
            elif any(word in text_lower for word in ['weld', 'join']):
                suggestions.extend([
                    "weld steel frame joints",
                    "join metal components",
                    "arc weld seam"
                ])
            elif any(word in text_lower for word in ['assemble', 'build']):
                suggestions.extend([
                    "assemble electronic components",
                    "build modular parts",
                    "install screws precisely"
                ])
        
        # Speed suggestions
        if not self.extracted_parameters.get('speed_preference'):
            suggestions.extend([
                "fast and efficient",
                "slow and precise",
                "medium speed with accuracy"
            ])
        
        # Motion suggestions
        if not self.extracted_parameters.get('motion_preference'):
            suggestions.extend([
                "smooth curved motion",
                "direct linear path",
                "careful precise movements"
            ])
        
        self.guided_suggestions = suggestions[:5]  # Limit to 5 suggestions
        return self.guided_suggestions
    
    def finalize_parameters(self, context) -> Dict[str, Any]:
        """Finalize and return all configured parameters."""
        # Convert extracted parameters to animation configuration
        config = {
            'task_type': self.extracted_parameters.get('task_type', 'pick_and_place'),
            'speed_multiplier': self._convert_speed_preference(),
            'motion_type': self.extracted_parameters.get('motion_preference', 'linear'),
            'precision_level': self._determine_precision_level(),
            'safety_enabled': True,
            'visualization': {
                'show_path': True,
                'show_coordinates': True,
                'highlight_objects': True
            },
            'animation': {
                'duration': self._calculate_animation_duration(),
                'frame_rate': 24,
                'interpolation': 'bezier' if self.extracted_parameters.get('motion_preference') == 'curved' else 'linear'
            }
        }
        
        # Add object-specific parameters
        if 'target_object' in self.extracted_parameters:
            config['target_object'] = self.extracted_parameters['target_object']
        
        if 'quantity' in self.extracted_parameters:
            config['repetitions'] = self.extracted_parameters['quantity']
        
        # End conversation
        context.scene.ai_assistant.conversation_active = False
        
        return config
    
    def _convert_speed_preference(self) -> float:
        """Convert speed preference to multiplier."""
        speed_map = {
            'slow': 0.5,
            'medium': 1.0,
            'fast': 2.0
        }
        return speed_map.get(self.extracted_parameters.get('speed_preference', 'medium'), 1.0)
    
    def _determine_precision_level(self) -> str:
        """Determine precision level based on task and preferences."""
        task = self.extracted_parameters.get('task_type', '')
        motion = self.extracted_parameters.get('motion_preference', '')
        
        if task in ['assembly', 'welding'] or motion == 'precise':
            return 'high'
        elif task in ['pick_and_place'] and motion == 'curved':
            return 'medium'
        else:
            return 'medium'
    
    def _calculate_animation_duration(self) -> float:
        """Calculate appropriate animation duration."""
        base_duration = 5.0  # seconds
        
        speed_pref = self.extracted_parameters.get('speed_preference', 'medium')
        speed_multipliers = {'slow': 1.5, 'medium': 1.0, 'fast': 0.7}
        
        quantity = self.extracted_parameters.get('quantity', 1)
        
        return base_duration * speed_multipliers[speed_pref] * quantity


# Blender Operators
class ROBOTANIM_OT_start_ai_assistant(Operator):
    """Start AI Parameter Assistant conversation"""
    bl_idname = "robotanim.start_ai_assistant"
    bl_label = "Start AI Assistant"
    bl_description = "Begin conversation with AI assistant to configure animation parameters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Initialize AI assistant
        if not hasattr(bpy.types.Scene, '_ai_assistant_instance'):
            bpy.types.Scene._ai_assistant_instance = AIParameterAssistant()
        
        assistant = bpy.types.Scene._ai_assistant_instance
        
        # Start conversation
        question = assistant.start_conversation(context)
        
        self.report({'INFO'}, "AI Assistant: " + question)
        return {'FINISHED'}


class ROBOTANIM_OT_respond_to_ai(Operator):
    """Submit response to AI assistant"""
    bl_idname = "robotanim.respond_to_ai"
    bl_label = "Submit Response"
    bl_description = "Submit your response to the AI assistant"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not hasattr(bpy.types.Scene, '_ai_assistant_instance'):
            self.report({'ERROR'}, "AI Assistant not initialized")
            return {'CANCELLED'}
        
        assistant = bpy.types.Scene._ai_assistant_instance
        user_response = context.scene.ai_assistant.user_response
        
        if not user_response.strip():
            self.report({'WARNING'}, "Please enter a response")
            return {'CANCELLED'}
        
        # Process response
        result = assistant.process_user_response(user_response, context)
        
        # Clear user input
        context.scene.ai_assistant.user_response = ""
        
        # Show next question
        if result['phase'] == 'confirmation':
            # Ready to finalize
            self.report({'INFO'}, "AI Assistant: " + result['question'])
        else:
            self.report({'INFO'}, "AI Assistant: " + result['question'])
        
        return {'FINISHED'}


class ROBOTANIM_OT_finalize_ai_setup(Operator):
    """Finalize AI assistant setup and generate parameters"""
    bl_idname = "robotanim.finalize_ai_setup"
    bl_label = "Generate Animation"
    bl_description = "Finalize AI setup and generate animation with configured parameters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not hasattr(bpy.types.Scene, '_ai_assistant_instance'):
            self.report({'ERROR'}, "AI Assistant not initialized")
            return {'CANCELLED'}
        
        assistant = bpy.types.Scene._ai_assistant_instance
        
        # Finalize parameters
        config = assistant.finalize_parameters(context)
        
        # Store configuration for scene building
        context.scene['ai_animation_config'] = config
        
        self.report({'INFO'}, f"AI Setup Complete! Generated {config['task_type']} animation with {config['animation']['duration']}s duration")
        
        # Trigger scene building
        bpy.ops.robotanim.build_ai_scene()
        
        return {'FINISHED'}


# Registration
ai_assistant_classes = [
    ParameterAssistantProperties,
    ROBOTANIM_OT_start_ai_assistant,
    ROBOTANIM_OT_respond_to_ai,
    ROBOTANIM_OT_finalize_ai_setup,
]


def register_ai_assistant():
    """Register AI assistant classes."""
    for cls in ai_assistant_classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    bpy.types.Scene.ai_assistant = bpy.props.PointerProperty(type=ParameterAssistantProperties)


def unregister_ai_assistant():
    """Unregister AI assistant classes."""
    # Clean up instance
    if hasattr(bpy.types.Scene, '_ai_assistant_instance'):
        delattr(bpy.types.Scene, '_ai_assistant_instance')
    
    # Unregister properties
    del bpy.types.Scene.ai_assistant
    
    # Unregister classes
    for cls in reversed(ai_assistant_classes):
        bpy.utils.unregister_class(cls) 