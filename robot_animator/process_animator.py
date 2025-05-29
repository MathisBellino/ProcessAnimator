#!/usr/bin/env python3
"""
ProcessAnimator - Main orchestrator for collaborative robot animation system

This module provides the primary interface for the ProcessAnimator system,
coordinating natural language processing, UI generation, collaborative questioning,
and iterative animation pipeline.
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List

from .ui.dynamic_ui import DynamicUI
from .questioning.collaborative_questioner import CollaborativeQuestioner
from .animation.axis_highlighter import AxisHighlighter
from .animation.iterative_animator import IterativeAnimator
from .ai.motion_planner import MotionPlanner
from .blender.scene_manager import BlenderSceneManager

logger = logging.getLogger(__name__)


class ProcessAnimator:
    """
    Main ProcessAnimator class for collaborative robot animation generation.
    
    Coordinates the entire workflow from natural language input to animated
    robot visualization with customized UI and collaborative refinement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ProcessAnimator with optional configuration.
        
        Args:
            config: Optional configuration dictionary for customizing behavior
        """
        self.config = config or self._default_config()
        
        # Initialize core components
        self.ui_generator = DynamicUI(self.config.get('ui_config', {}))
        self.questioner = CollaborativeQuestioner(self.config.get('questioning_config', {}))
        self.axis_highlighter = AxisHighlighter(self.config.get('highlighting_config', {}))
        self.iterative_animator = IterativeAnimator(self.config.get('animation_config', {}))
        
        # Initialize existing components for integration
        self.motion_planner = MotionPlanner()
        self.scene_manager = BlenderSceneManager()
        
        # State tracking
        self.current_process_data = {}
        self.questioning_history = []
        self.animation_state = 'idle'
        
        logger.info("ProcessAnimator initialized successfully")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for ProcessAnimator."""
        return {
            'max_questioning_iterations': 3,
            'enable_real_time_preview': True,
            'default_animation_quality': 'low',
            'collaborative_mode': True,
            'auto_highlight_axis': True,
            'ui_update_interval': 1.0,
            'supported_processes': [
                'assembly', 'welding', 'painting', 'pick_and_place',
                'packaging', 'quality_inspection', 'material_handling'
            ],
            'supported_robots': [
                'ABB', 'KUKA', 'FANUC', 'Universal Robots', 'Yaskawa',
                'Kawasaki', 'Staubli', 'Mitsubishi'
            ]
        }
    
    def animate(self, input_description: str) -> Dict[str, Any]:
        """
        Main entry point for the animation process.
        
        Args:
            input_description: Natural language description of the robot process
            
        Returns:
            Dictionary containing animation results and status
        """
        try:
            logger.info(f"Starting animation process for: {input_description}")
            
            # Step 1: Process natural language input
            process_data = self.process_natural_language(input_description)
            if not process_data['success']:
                return process_data
            
            self.current_process_data = process_data
            
            # Step 2: Generate customized UI
            ui_result = self._generate_ui(process_data)
            
            # Step 3: Start collaborative questioning
            questioning_result = self._start_questioning(process_data)
            
            # Step 4: Highlight animation axis in blue
            axis_result = self._highlight_animation_axis(process_data)
            
            # Step 5: Start iterative animation
            animation_result = self._start_iterative_animation(process_data)
            
            # Compile final result
            result = {
                'success': True,
                'process_type': process_data['process_type'],
                'robot_type': process_data['robot_type'],
                'ui_generated': ui_result,
                'questioning_complete': questioning_result,
                'axis_highlighted': axis_result,
                'animation_started': animation_result,
                'iterations_completed': len(self.questioning_history),
                'animation_ready': True,
                'timestamp': time.time()
            }
            
            logger.info("Animation process completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in animation process: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': self._get_error_suggestions(str(e))
            }
    
    def process_natural_language(self, input_text: str) -> Dict[str, Any]:
        """
        Process natural language input to extract robot and process information.
        
        Args:
            input_text: Raw natural language description
            
        Returns:
            Dictionary containing extracted process parameters
        """
        if not input_text or not isinstance(input_text, str):
            return {
                'success': False,
                'error': 'Invalid input: Please provide a valid text description'
            }
        
        try:
            # Clean and normalize input
            cleaned_input = input_text.lower().strip()
            
            # Extract robot type
            robot_type = self._extract_robot_type(cleaned_input)
            
            # Extract process type
            process_type = self._extract_process_type(cleaned_input)
            
            # Extract target object
            target_object = self._extract_target_object(cleaned_input)
            
            # Extract environment
            environment = self._extract_environment(cleaned_input)
            
            # Validate required information
            if not robot_type or not process_type:
                return {
                    'success': False,
                    'error': 'Could not identify robot type or process type',
                    'clarification_needed': True
                }
            
            result = {
                'success': True,
                'robot_type': robot_type,
                'process_type': process_type,
                'target_object': target_object,
                'environment': environment,
                'raw_input': input_text,
                'confidence_score': self._calculate_confidence(robot_type, process_type, target_object)
            }
            
            logger.info(f"Successfully parsed: {robot_type} performing {process_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing natural language: {str(e)}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}'
            }
    
    def _extract_robot_type(self, text: str) -> str:
        """Extract robot type from input text."""
        # Pattern for specific robot models
        robot_patterns = [
            r'(abb\s+irb\s+\d+)',
            r'(kuka\s+kr\s+\d+)',
            r'(fanuc\s+[a-z]+\d*)',
            r'(universal\s+robots?\s+ur\d+)',
            r'(ur\d+)',
            r'(yaskawa\s+[a-z]+\d*)',
            r'(kawasaki\s+[a-z]+\d*)',
            r'(staubli\s+[a-z]+\d*)',
            r'(mitsubishi\s+[a-z]+\d*)',
            r'(robot\s+[a-z]\w*)',  # Generic robot X, robot Y, etc.
        ]
        
        for pattern in robot_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).title()
        
        # Fallback to generic robot if "robot" is mentioned
        if 'robot' in text:
            robot_match = re.search(r'robot\s+(\w+)', text)
            if robot_match:
                return f"Robot {robot_match.group(1).upper()}"
            return "Generic Robot"
        
        return ""
    
    def _extract_process_type(self, text: str) -> str:
        """Extract process type from input text."""
        process_keywords = {
            'assembly': ['assemble', 'assembly', 'build', 'construct', 'mount'],
            'welding': ['weld', 'welding', 'joining', 'fuse'],
            'painting': ['paint', 'painting', 'spray', 'coating'],
            'pick_and_place': ['pick', 'place', 'pick and place', 'transfer', 'move'],
            'packaging': ['package', 'packaging', 'box', 'wrap'],
            'quality_inspection': ['inspect', 'inspection', 'check', 'quality'],
            'material_handling': ['handle', 'handling', 'transport', 'carry']
        }
        
        for process, keywords in process_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return process
        
        return ""
    
    def _extract_target_object(self, text: str) -> str:
        """Extract target object from input text."""
        # Look for common manufacturing objects
        object_patterns = [
            r'(bike\s+frame)',
            r'(automotive\s+chassis)',
            r'(car\s+body\s+panels?)',
            r'(electronic\s+components?)',
            r'(steel\s+frame)',
            r'(small\s+parts?)',
            r'(\w+\s+frame)',
            r'(\w+\s+components?)',
            r'(\w+\s+parts?)'
        ]
        
        for pattern in object_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "components"
    
    def _extract_environment(self, text: str) -> str:
        """Extract environment/setting from input text."""
        environment_patterns = [
            r'(manufacturing\s+plant)',
            r'(assembly\s+line)',
            r'(production\s+setting)',
            r'(factory\s+floor)',
            r'(clean\s+room)',
            r'(warehouse)',
            r'(laboratory)',
            r'(automotive\s+plant)',
            r'(\w+\s+assembly\s+line)'
        ]
        
        for pattern in environment_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "industrial setting"
    
    def _calculate_confidence(self, robot_type: str, process_type: str, target_object: str) -> float:
        """Calculate confidence score for extracted information."""
        score = 0.0
        
        if robot_type and robot_type != "Generic Robot":
            score += 0.4
        elif robot_type:
            score += 0.2
        
        if process_type:
            score += 0.4
        
        if target_object and target_object != "components":
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_ui(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customized UI for the specific process."""
        try:
            ui_config = self.ui_generator.generate_ui(process_data)
            logger.info(f"Generated {ui_config['ui_type']} interface")
            return ui_config
        except Exception as e:
            logger.error(f"UI generation failed: {str(e)}")
            return {'error': str(e)}
    
    def _start_questioning(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start collaborative questioning process."""
        try:
            questioning_result = {'iterations': 0, 'final_parameters': {}}
            
            for iteration in range(1, self.config['max_questioning_iterations'] + 1):
                question = self.questioner.generate_question(process_data, iteration)
                if not question:
                    break
                
                # In a real implementation, this would wait for user input
                # For now, we'll simulate the questioning process
                self.questioning_history.append({
                    'iteration': iteration,
                    'question': question,
                    'timestamp': time.time()
                })
                
                questioning_result['iterations'] = iteration
            
            logger.info(f"Completed {questioning_result['iterations']} questioning iterations")
            return questioning_result
            
        except Exception as e:
            logger.error(f"Questioning failed: {str(e)}")
            return {'error': str(e)}
    
    def _highlight_animation_axis(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Highlight main animation axis in blue."""
        try:
            # Add position data for axis determination
            process_data_with_positions = process_data.copy()
            process_data_with_positions.update({
                'robot_position': (0, 0, 1),
                'target_positions': [(0.5, 0.3, 0.8), (0.2, -0.4, 0.6)],
                'workspace_bounds': {'x': (-1, 1), 'y': (-1, 1), 'z': (0, 2)}
            })
            
            axis_data = self.axis_highlighter.determine_main_axis(process_data_with_positions)
            highlight_result = self.axis_highlighter.highlight_in_blender(axis_data)
            
            logger.info(f"Highlighted {axis_data['primary_axis']} axis in blue")
            return highlight_result
            
        except Exception as e:
            logger.error(f"Axis highlighting failed: {str(e)}")
            return {'error': str(e)}
    
    def _start_iterative_animation(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start iterative animation pipeline with low quality first."""
        try:
            animation_config = {
                'process_type': process_data['process_type'],
                'robot_type': process_data['robot_type'],
                'quality_level': self.config['default_animation_quality'],
                'robot_positions': [(0, 0, 1), (0.5, 0.3, 0.8)],
                'animation_duration': 10.0
            }
            
            animation_result = self.iterative_animator.start_animation(animation_config)
            self.animation_state = 'running'
            
            logger.info(f"Started {animation_config['quality_level']} quality animation")
            return animation_result
            
        except Exception as e:
            logger.error(f"Animation start failed: {str(e)}")
            return {'error': str(e)}
    
    def _get_error_suggestions(self, error_msg: str) -> List[str]:
        """Get helpful suggestions based on error message."""
        suggestions = []
        
        if 'robot type' in error_msg.lower():
            suggestions.append("Try specifying a robot model like 'ABB IRB 6700' or 'Universal Robots UR5'")
            suggestions.append("Or use generic terms like 'industrial robot' or 'robot arm'")
        
        if 'process type' in error_msg.lower():
            suggestions.append("Specify the operation: assembly, welding, painting, pick and place, etc.")
            suggestions.append("Example: 'Robot welding steel frames in automotive plant'")
        
        if not suggestions:
            suggestions.append("Try providing more details about the robot and the manufacturing process")
            suggestions.append("Example: 'KUKA robot assembling car parts in assembly line'")
        
        return suggestions
    
    def get_animation_status(self) -> Dict[str, Any]:
        """Get current animation status and progress."""
        return {
            'state': self.animation_state,
            'process_data': self.current_process_data,
            'questioning_iterations': len(self.questioning_history),
            'last_update': time.time()
        }
    
    def update_animation_quality(self, quality_level: str) -> Dict[str, Any]:
        """Update animation quality during iteration."""
        if quality_level not in ['low', 'medium', 'high']:
            return {'success': False, 'error': 'Invalid quality level'}
        
        try:
            result = self.iterative_animator.update_quality(quality_level)
            logger.info(f"Updated animation quality to {quality_level}")
            return result
        except Exception as e:
            logger.error(f"Quality update failed: {str(e)}")
            return {'success': False, 'error': str(e)} 