import pytest
import sys
import os

# Mock bpy module for testing
class MockBpy:
    class ops:
        @staticmethod
        def object():
            pass
    
    class types:
        class Object:
            pass
    
    class context:
        scene = None
        object = None

# Mock mathutils module for testing
class MockMathutils:
    class Vector:
        def __init__(self, *args, **kwargs):
            pass
    class Matrix:
        def __init__(self, *args, **kwargs):
            pass
    class Euler:
        def __init__(self, *args, **kwargs):
            pass

# Mock bmesh module for testing
class MockBmesh:
    pass

# Mock gpu module for testing
class MockGpu:
    pass

# Add mock modules to sys.modules
sys.modules['bpy'] = MockBpy()
sys.modules['mathutils'] = MockMathutils()
sys.modules['bmesh'] = MockBmesh()
sys.modules['gpu'] = MockGpu()

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) 