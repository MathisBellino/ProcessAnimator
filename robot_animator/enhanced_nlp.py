import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import re
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedNLProcessor:
    def __init__(self):
        """Initialize the enhanced natural language processor."""
        # Load the lightweight sentence transformer model
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load spaCy for entity recognition
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Pre-defined command patterns with semantic variations
        self.command_patterns = {
            'pick_and_place': [
                "pick up the object and place it on the location",
                "grab the object and put it on the location",
                "take the object and set it on the location",
                "lift the object and place it at the location",
                "pick up object and place on location",
                "grab object and put on location",
                "take object and set on location",
                "pick the object place the location",
                "get the object put the location"
            ],
            'move_to': [
                "move to the location",
                "go to the location", 
                "navigate to the location",
                "travel to the location",
                "move to location",
                "go to location",
                "head to location"
            ],
            'grab': [
                "grab the object",
                "pick up the object",
                "take the object",
                "lift the object",
                "grab object",
                "pick object",
                "take object",
                "get object"
            ],
            'place': [
                "place the object on the location",
                "put the object on the location",
                "set the object on the location",
                "drop the object at the location",
                "place object on location",
                "put object on location",
                "set object on location"
            ]
        }
        
        # Pre-compute embeddings for all pattern variations
        self.pattern_embeddings = self._precompute_pattern_embeddings()
        
        # Confidence thresholds
        self.similarity_threshold = 0.3
        self.entity_confidence_threshold = 0.6

    def _precompute_pattern_embeddings(self) -> Dict[str, np.ndarray]:
        """Pre-compute embeddings for all command patterns."""
        embeddings = {}
        for intent, patterns in self.command_patterns.items():
            embeddings[intent] = self.sentence_model.encode(patterns)
        return embeddings

    def parse_command(self, command: str) -> Dict:
        """
        Parse a natural language command into structured actions.
        
        Args:
            command (str): The natural language command to parse
            
        Returns:
            Dict: Structured command with intent, entities, and confidence scores
        """
        # Get command embedding
        command_embedding = self.sentence_model.encode([command])[0]
        
        # Find best matching intent
        best_intent = None
        best_similarity = -1
        
        for intent, embeddings in self.pattern_embeddings.items():
            similarities = cosine_similarity([command_embedding], embeddings)[0]
            max_similarity = np.max(similarities)
            
            if max_similarity > best_similarity:
                best_similarity = max_similarity
                best_intent = intent
        
        # Extract entities using spaCy
        doc = self.nlp(command)
        entities = self._extract_entities(doc)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(best_similarity, entities)
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'entities': entities,
            'raw_command': command,
            'similarity_score': float(best_similarity)
        }

    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract entities from the command using spaCy."""
        entities = {
            'objects': [],
            'locations': [],
            'actions': []
        }
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "WORK_OF_ART"]:
                entities['objects'].append(ent.text)
            elif ent.label_ in ["LOC", "ORG", "FAC"]:
                entities['locations'].append(ent.text)
        
        # Extract nouns as potential objects and locations
        nouns = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        
        # Common object words
        object_words = ['cube', 'box', 'sphere', 'block', 'part', 'piece', 'item', 'thing']
        location_words = ['table', 'shelf', 'floor', 'corner', 'position', 'place', 'spot', 'area']
        
        for noun in nouns:
            if noun.lower() in object_words or any(obj_word in noun.lower() for obj_word in object_words):
                entities['objects'].append(noun)
            elif noun.lower() in location_words or any(loc_word in noun.lower() for loc_word in location_words):
                entities['locations'].append(noun)
            elif not entities['objects']:  # If no specific objects found, treat nouns as objects
                entities['objects'].append(noun)
        
        # Extract verbs as potential actions
        entities['actions'] = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        
        # Remove duplicates while preserving order
        entities['objects'] = list(dict.fromkeys(entities['objects']))
        entities['locations'] = list(dict.fromkeys(entities['locations']))
        entities['actions'] = list(dict.fromkeys(entities['actions']))
        
        return entities

    def _calculate_confidence(self, similarity: float, entities: Dict) -> float:
        """Calculate overall confidence score."""
        # Base confidence on semantic similarity
        confidence = similarity
        
        # Adjust confidence based on entity presence
        if entities['objects'] or entities['locations']:
            confidence *= 1.1  # Boost confidence if entities are found
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)

    def get_action_sequence(self, parsed_command: Dict) -> List[Dict]:
        """
        Convert parsed command into a sequence of robot actions.
        
        Args:
            parsed_command (Dict): The parsed command from parse_command()
            
        Returns:
            List[Dict]: Sequence of robot actions to execute
        """
        actions = []
        
        if parsed_command['confidence'] < self.similarity_threshold:
            logger.warning(f"Low confidence command: {parsed_command['raw_command']}")
            return actions
        
        intent = parsed_command['intent']
        entities = parsed_command['entities']
        
        if intent == 'pick_and_place':
            if len(entities['objects']) > 0 and len(entities['locations']) > 0:
                actions.extend([
                    {'action': 'move_to', 'target': entities['objects'][0]},
                    {'action': 'grab', 'target': entities['objects'][0]},
                    {'action': 'move_to', 'target': entities['locations'][0]},
                    {'action': 'place', 'target': entities['objects'][0], 'location': entities['locations'][0]}
                ])
        
        elif intent == 'move_to':
            if len(entities['locations']) > 0:
                actions.append({
                    'action': 'move_to',
                    'target': entities['locations'][0]
                })
        
        elif intent == 'grab':
            if len(entities['objects']) > 0:
                actions.extend([
                    {'action': 'move_to', 'target': entities['objects'][0]},
                    {'action': 'grab', 'target': entities['objects'][0]}
                ])
        
        elif intent == 'place':
            if len(entities['objects']) > 0 and len(entities['locations']) > 0:
                actions.extend([
                    {'action': 'move_to', 'target': entities['locations'][0]},
                    {'action': 'place', 'target': entities['objects'][0], 'location': entities['locations'][0]}
                ])
        
        return actions

    def process_command(self, command: str) -> Dict:
        """
        Process a natural language command and return structured actions.
        
        Args:
            command (str): The natural language command
            
        Returns:
            Dict: Complete processing result with actions and metadata
        """
        parsed = self.parse_command(command)
        actions = self.get_action_sequence(parsed)
        
        return {
            'success': len(actions) > 0,
            'parsed_command': parsed,
            'actions': actions,
            'confidence': parsed['confidence']
        } 