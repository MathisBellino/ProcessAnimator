#!/usr/bin/env python3
"""
Manufacturing module for ProcessAnimator

Contains smart scaling, robot analysis, and GCODE generation.
"""

from .smart_scaler import SmartScaler
from .robot_analyzer import RobotAnalyzer
from .gcode_generator import GCodeGenerator

__all__ = [
    'SmartScaler',
    'RobotAnalyzer',
    'GCodeGenerator'
] 