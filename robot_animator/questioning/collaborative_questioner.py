#!/usr/bin/env python3
"""
Collaborative Questioner for ProcessAnimator

Generates collaborative, short-sentence questions to refine animation parameters
through iterative dialogue with maximum 3 iterations.
"""

import logging
import random
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class CollaborativeQuestioner:
    """
    Collaborative questioning system for refining robot animation parameters.
    
    Asks short, collaborative questions to gather specific details about
    the animation requirements in a maximum of 3 iterations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CollaborativeQuestioner.
        
        Args:
            config: Optional configuration for questioning behavior
        """
        self.config = config or self._default_config()
        self.question_templates = self._load_question_templates()
        self.process_specific_questions = self._load_process_questions()
        self.collaborative_phrases = self._load_collaborative_phrases()
        
        logger.info("CollaborativeQuestioner initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for questioning."""
        return {
            'max_iterations': 3,
            'max_words_per_question': 15,
            'collaborative_tone': True,
            'adaptive_questioning': True,
            'prioritize_critical_params': True
        }
    
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates categorized by type."""
        return {
            'clarification': [
                "What speed would you prefer?",
                "Should we focus on precision or speed?",
                "Any specific safety requirements?",
                "What's the priority here?",
                "How detailed should this be?"
            ],
            'specification': [
                "Where should the robot start?",
                "What's the target position?",
                "How many cycles do you need?",
                "What's the grip force setting?",
                "Which direction first?"
            ],
            'preference': [
                "Would you like smooth or fast motion?",
                "Show the process step-by-step?",
                "Add collision avoidance?",
                "Include safety zones?",
                "Want multiple camera angles?"
            ],
            'validation': [
                "Does this look right to you?",
                "Should we adjust anything?",
                "Happy with the timing?",
                "Need any changes?",
                "Ready to proceed?"
            ]
        }
    
    def _load_process_questions(self) -> Dict[str, Dict[str, List[str]]]:
        """Load process-specific question sets."""
        return {
            'assembly': {
                'iteration_1': [
                    "What's the assembly sequence?",
                    "How tight should the connections be?",
                    "Should we show component alignment?",
                    "Any specific tools needed?"
                ],
                'iteration_2': [
                    "Want to see joint details?",
                    "Include quality checkpoints?",
                    "Show torque specifications?",
                    "Add part identification labels?"
                ],
                'iteration_3': [
                    "Adjust the assembly speed?",
                    "Need error handling demos?",
                    "Show different orientations?",
                    "Add final inspection step?"
                ]
            },
            'welding': {
                'iteration_1': [
                    "What welding technique should we use?",
                    "How hot should the arc be?",
                    "Show the seam path clearly?",
                    "Include safety sparks visualization?"
                ],
                'iteration_2': [
                    "Want to see penetration depth?",
                    "Include cooling phase?",
                    "Show gas flow patterns?",
                    "Add temperature monitoring?"
                ],
                'iteration_3': [
                    "Adjust torch angle dynamics?",
                    "Show multi-pass welding?",
                    "Include defect detection?",
                    "Add post-weld inspection?"
                ]
            },
            'painting': {
                'iteration_1': [
                    "What spray pattern works best?",
                    "How thick should the coating be?",
                    "Show overspray areas?",
                    "Include color mixing visualization?"
                ],
                'iteration_2': [
                    "Want to see coverage analysis?",
                    "Include drying time simulation?",
                    "Show booth airflow?",
                    "Add thickness measurements?"
                ],
                'iteration_3': [
                    "Adjust spray pressure settings?",
                    "Show multiple coat layers?",
                    "Include quality inspection?",
                    "Add efficiency metrics?"
                ]
            }
        }
    
    def _load_collaborative_phrases(self) -> Dict[str, List[str]]:
        """Load collaborative language phrases."""
        return {
            'starters': [
                "Let's", "How about we", "Shall we", "What if we",
                "Would you like to", "Let's try", "Should we"
            ],
            'connectors': [
                "together", "collaboratively", "as a team",
                "working together", "jointly"
            ],
            'preferences': [
                "What do you think about", "Your preference for",
                "How would you like", "What works better for you",
                "Would you prefer"
            ],
            'feedback': [
                "Does this feel right?", "What's your take?",
                "How does this look?", "Thoughts on this?",
                "Your feedback?"
            ]
        }
    
    def generate_question(self, process_data: Dict[str, Any], iteration: int) -> Optional[Dict[str, Any]]:
        """
        Generate a collaborative question for the given iteration.
        
        Args:
            process_data: Current process information
            iteration: Question iteration number (1-3)
            
        Returns:
            Dictionary containing question details or None if max iterations exceeded
        """
        if iteration > self.config['max_iterations']:
            return None
        
        try:
            process_type = process_data.get('process_type', 'assembly')
            robot_type = process_data.get('robot_type', 'Generic Robot')
            
            # Determine question category based on iteration
            question_category = self._get_question_category(iteration)
            
            # Generate question text
            question_text = self._generate_question_text(
                process_type, iteration, question_category, process_data
            )
            
            # Determine specificity level
            specificity_level = self._get_specificity_level(iteration)
            
            # Determine expected response type
            response_type = self._get_expected_response_type(question_category, iteration)
            
            question = {
                'iteration': iteration,
                'type': question_category,
                'text': question_text,
                'specificity_level': specificity_level,
                'expected_response_type': response_type,
                'tone': 'collaborative',
                'process_context': process_type,
                'robot_context': robot_type,
                'max_words': self.config['max_words_per_question'],
                'timestamp': logging.time.time()
            }
            
            logger.info(f"Generated question {iteration}: {question_text}")
            return question
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            return None
    
    def _get_question_category(self, iteration: int) -> str:
        """Determine question category based on iteration."""
        if iteration == 1:
            return random.choice(['clarification', 'specification'])
        elif iteration == 2:
            return random.choice(['specification', 'preference'])
        else:  # iteration == 3
            return 'validation'
    
    def _get_specificity_level(self, iteration: int) -> str:
        """Determine specificity level based on iteration."""
        if iteration == 1:
            return 'broad'
        elif iteration == 2:
            return 'focused'
        else:
            return 'specific'
    
    def _get_expected_response_type(self, category: str, iteration: int) -> str:
        """Determine expected response type."""
        if category == 'clarification':
            return 'description'
        elif category == 'specification':
            return 'choice' if iteration <= 2 else 'number'
        elif category == 'preference':
            return 'choice'
        else:  # validation
            return 'boolean'
    
    def _generate_question_text(self, process_type: str, iteration: int, 
                               category: str, process_data: Dict[str, Any]) -> str:
        """Generate the actual question text."""
        
        # Try process-specific questions first
        if process_type in self.process_specific_questions:
            iteration_key = f'iteration_{iteration}'
            if iteration_key in self.process_specific_questions[process_type]:
                process_questions = self.process_specific_questions[process_type][iteration_key]
                base_question = random.choice(process_questions)
                return self._add_collaborative_tone(base_question)
        
        # Fall back to generic questions
        if category in self.question_templates:
            base_question = random.choice(self.question_templates[category])
            return self._add_collaborative_tone(base_question)
        
        # Generate contextual question
        return self._generate_contextual_question(process_type, category, process_data)
    
    def _add_collaborative_tone(self, question: str) -> str:
        """Add collaborative tone to question."""
        if not self.config['collaborative_tone']:
            return question
        
        # Randomly add collaborative starters
        if random.random() < 0.7:  # 70% chance to add collaborative tone
            if question.lower().startswith(('what', 'how', 'which', 'should', 'would')):
                starters = self.collaborative_phrases['starters']
                starter = random.choice(starters)
                
                # Adapt the question structure
                if starter in ['Let\'s', 'Shall we']:
                    if question.startswith('What'):
                        question = question.replace('What', 'decide what', 1)
                    elif question.startswith('How'):
                        question = question.replace('How', 'figure out how', 1)
                    elif question.startswith('Should'):
                        question = question.replace('Should we', '', 1).strip()
                
                question = f"{starter} {question.lower()}"
            
            # Add feedback phrases for validation questions
            elif any(phrase in question.lower() for phrase in ['does this', 'should we', 'need any']):
                feedback_phrases = self.collaborative_phrases['feedback']
                if random.random() < 0.5:
                    feedback = random.choice(feedback_phrases)
                    question = f"{question} {feedback}"
        
        return question
    
    def _generate_contextual_question(self, process_type: str, category: str, 
                                     process_data: Dict[str, Any]) -> str:
        """Generate contextual question based on process data."""
        robot_type = process_data.get('robot_type', 'robot')
        target_object = process_data.get('target_object', 'components')
        
        contextual_questions = {
            'assembly': {
                'clarification': f"How should the {robot_type} handle the {target_object}?",
                'specification': f"What's the ideal grip for {target_object}?",
                'preference': f"Show detailed {target_object} alignment?",
                'validation': f"Happy with the {target_object} assembly sequence?"
            },
            'welding': {
                'clarification': f"What weld quality do you need?",
                'specification': f"Which welding speed works best?",
                'preference': f"Include sparks and heat effects?",
                'validation': f"Satisfied with the weld pattern?"
            },
            'painting': {
                'clarification': f"What coverage level do you want?",
                'specification': f"How many paint layers needed?",
                'preference': f"Show paint thickness visualization?",
                'validation': f"Good with the spray pattern?"
            }
        }
        
        if process_type in contextual_questions and category in contextual_questions[process_type]:
            return contextual_questions[process_type][category]
        
        # Fallback generic question
        return "What would you like to adjust?"
    
    def process_response(self, question: Dict[str, Any], user_response: str) -> Dict[str, Any]:
        """
        Process user response to extract parameters.
        
        Args:
            question: The question that was asked
            user_response: User's response text
            
        Returns:
            Dictionary containing processed response and extracted parameters
        """
        try:
            # Clean and normalize response
            cleaned_response = user_response.lower().strip()
            
            # Extract parameters based on response type
            extracted_params = {}
            
            # Extract speed preferences
            speed_keywords = {
                'slow': ['slow', 'slowly', 'careful', 'cautious'],
                'medium': ['medium', 'normal', 'standard', 'moderate'],
                'fast': ['fast', 'quick', 'rapid', 'speed']
            }
            
            for speed, keywords in speed_keywords.items():
                if any(keyword in cleaned_response for keyword in keywords):
                    extracted_params['speed'] = speed
                    break
            
            # Extract priority preferences
            if any(word in cleaned_response for word in ['safety', 'safe', 'careful']):
                extracted_params['priority'] = 'safety'
            elif any(word in cleaned_response for word in ['precision', 'accurate', 'exact']):
                extracted_params['priority'] = 'precision'
            elif any(word in cleaned_response for word in ['speed', 'fast', 'efficiency']):
                extracted_params['priority'] = 'speed'
            
            # Extract yes/no responses
            if any(word in cleaned_response for word in ['yes', 'yeah', 'sure', 'ok', 'good']):
                extracted_params['confirmation'] = True
            elif any(word in cleaned_response for word in ['no', 'nope', 'not', 'don\'t']):
                extracted_params['confirmation'] = False
            
            # Extract detail level preferences
            if any(word in cleaned_response for word in ['detail', 'detailed', 'step', 'show']):
                extracted_params['detail_level'] = 'high'
            elif any(word in cleaned_response for word in ['simple', 'basic', 'quick']):
                extracted_params['detail_level'] = 'low'
            
            # Extract numerical values
            numbers = re.findall(r'\d+(?:\.\d+)?', cleaned_response)
            if numbers:
                extracted_params['numerical_value'] = float(numbers[0])
            
            result = {
                'success': True,
                'question_id': question.get('iteration', 0),
                'raw_response': user_response,
                'cleaned_response': cleaned_response,
                'extracted_parameters': extracted_params,
                'response_type': question.get('expected_response_type', 'unknown'),
                'processing_timestamp': logging.time.time()
            }
            
            logger.info(f"Processed response: {len(extracted_params)} parameters extracted")
            return result
            
        except Exception as e:
            logger.error(f"Response processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question_id': question.get('iteration', 0)
            }
    
    def get_user_response(self, question: Dict[str, Any]) -> str:
        """
        Get user response to question. In a real implementation, this would
        wait for user input. For testing, returns simulated responses.
        
        Args:
            question: Question dictionary
            
        Returns:
            Simulated user response
        """
        # This is a mock implementation for testing
        # In a real system, this would interface with the UI
        
        simulated_responses = {
            1: ["Medium speed, safety first", "Show detailed steps", "Focus on precision"],
            2: ["Yes, include quality checks", "Make it smooth", "Add safety zones"],
            3: ["Looks good to me", "Maybe a bit faster", "Perfect, let's proceed"]
        }
        
        iteration = question.get('iteration', 1)
        if iteration in simulated_responses:
            return random.choice(simulated_responses[iteration])
        
        return "Looks good"
    
    def summarize_collected_parameters(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize all collected parameters from questioning session.
        
        Args:
            responses: List of processed responses
            
        Returns:
            Summary of all collected parameters
        """
        summary = {
            'total_iterations': len(responses),
            'collected_parameters': {},
            'user_preferences': {},
            'final_configuration': {}
        }
        
        # Aggregate all extracted parameters
        for response in responses:
            if response.get('success') and 'extracted_parameters' in response:
                summary['collected_parameters'].update(response['extracted_parameters'])
        
        # Determine final preferences
        params = summary['collected_parameters']
        
        if 'speed' in params:
            summary['user_preferences']['animation_speed'] = params['speed']
        
        if 'priority' in params:
            summary['user_preferences']['main_priority'] = params['priority']
        
        if 'detail_level' in params:
            summary['user_preferences']['detail_level'] = params['detail_level']
        
        if 'confirmation' in params:
            summary['user_preferences']['user_satisfied'] = params['confirmation']
        
        # Generate final configuration
        summary['final_configuration'] = {
            'animation_speed': params.get('speed', 'medium'),
            'priority_mode': params.get('priority', 'safety'),
            'detail_level': params.get('detail_level', 'medium'),
            'include_safety_features': True,
            'real_time_feedback': True
        }
        
        logger.info(f"Summarized {len(responses)} questioning iterations")
        return summary 