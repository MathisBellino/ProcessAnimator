from robot_animator.enhanced_nlp import EnhancedNLProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize the NLP processor
    logger.info("Initializing Enhanced NLP Processor...")
    nlp = EnhancedNLProcessor()
    
    # Example commands to test
    commands = [
        "pick up the red cube and place it on the table",
        "move to the corner",
        "grab the blue sphere",
        "place the cube on the shelf",
        "do something with that thing over there"  # This should have low confidence
    ]
    
    # Process each command
    for command in commands:
        logger.info(f"\nProcessing command: {command}")
        result = nlp.process_command(command)
        
        # Print results
        print("\nResults:")
        print(f"Success: {result['success']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Intent: {result['parsed_command']['intent']}")
        print("\nEntities:")
        for entity_type, entities in result['parsed_command']['entities'].items():
            if entities:
                print(f"  {entity_type}: {entities}")
        
        print("\nActions:")
        for action in result['actions']:
            print(f"  {action}")

if __name__ == "__main__":
    main() 