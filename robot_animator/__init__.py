"""
Robot Animator Plus Delux 3000

A comprehensive robotics development platform integrating Blender's 3D capabilities
with AI-driven motion planning and collaborative robot safety systems.

This package provides:
- Keyframe data processing for robot animations
- Blender integration for real-time 3D visualization
- AI-powered motion planning and natural language processing
- Collaborative robot safety monitoring
- End-to-end data flow pipeline from commands to robot control
- Process-specific animation with natural language input
- Collaborative questioning system for animation refinement
- Dynamic UI generation for different manufacturing processes
- Iterative animation with quality progression
"""

__version__ = "1.0.0"
__author__ = "Robot Animator Team"
__description__ = "AI-Powered Robotics Animation and Control Platform"

from .core.keyframe_processor import KeyframeProcessor
from .blender.scene_manager import BlenderSceneManager
from .ai.motion_planner import MotionPlanner
from .safety.cobot_monitor import CobotSafetyMonitor
from .pipeline.data_flow import DataFlowPipeline

# ProcessAnimator system components
from .process_animator import ProcessAnimator
from .ui.dynamic_ui import DynamicUI
from .questioning.collaborative_questioner import CollaborativeQuestioner
from .animation.axis_highlighter import AxisHighlighter
from .animation.iterative_animator import IterativeAnimator

__all__ = [
    "KeyframeProcessor",
    "BlenderSceneManager", 
    "MotionPlanner",
    "CobotSafetyMonitor",
    "DataFlowPipeline",
    "ProcessAnimator",
    "DynamicUI",
    "CollaborativeQuestioner",
    "AxisHighlighter",
    "IterativeAnimator"
] 