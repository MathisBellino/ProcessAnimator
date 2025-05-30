import pytest
from robot_animator.enhanced_nlp import EnhancedNLProcessor

@pytest.fixture
def nlp_processor():
    return EnhancedNLProcessor()

def test_basic_commands(nlp_processor):
    """Test basic command parsing."""
    commands = [
        "pick up the red cube and place it on the table",
        "move to the corner",
        "grab the blue sphere",
        "place the cube on the shelf"
    ]
    
    for command in commands:
        result = nlp_processor.process_command(command)
        assert result['success'] is True
        assert result['confidence'] > 0.7
        assert len(result['actions']) > 0

def test_entity_extraction(nlp_processor):
    """Test entity extraction from commands."""
    command = "pick up the red cube and place it on the wooden table"
    result = nlp_processor.process_command(command)
    
    assert 'objects' in result['parsed_command']['entities']
    assert 'locations' in result['parsed_command']['entities']
    assert len(result['parsed_command']['entities']['objects']) > 0
    assert len(result['parsed_command']['entities']['locations']) > 0

def test_confidence_calculation(nlp_processor):
    """Test confidence score calculation."""
    # High confidence command
    result1 = nlp_processor.process_command("pick up the cube and place it on the table")
    assert result1['confidence'] > 0.8
    
    # Low confidence command
    result2 = nlp_processor.process_command("do something with that thing over there")
    assert result2['confidence'] < 0.7

def test_action_sequence_generation(nlp_processor):
    """Test generation of action sequences."""
    command = "pick up the red cube and place it on the table"
    result = nlp_processor.process_command(command)
    
    actions = result['actions']
    assert len(actions) == 4  # move_to, grab, move_to, place
    assert actions[0]['action'] == 'move_to'
    assert actions[1]['action'] == 'grab'
    assert actions[2]['action'] == 'move_to'
    assert actions[3]['action'] == 'place'

def test_variations(nlp_processor):
    """Test different ways of expressing the same command."""
    variations = [
        "pick up the cube and place it on the table",
        "grab the cube and put it on the table",
        "take the cube and set it on the table",
        "lift the cube and place it at the table"
    ]
    
    for command in variations:
        result = nlp_processor.process_command(command)
        assert result['success'] is True
        assert result['confidence'] > 0.7
        assert len(result['actions']) == 4

def test_invalid_commands(nlp_processor):
    """Test handling of invalid or unclear commands."""
    invalid_commands = [
        "do something",
        "move that thing",
        "put it there",
        ""
    ]
    
    for command in invalid_commands:
        result = nlp_processor.process_command(command)
        assert result['success'] is False or result['confidence'] < 0.7 