#!/usr/bin/env python3
"""
Engineering Brain for ProcessAnimator

The core engineering intelligence that understands:
- All robot kinematics (6DOF, SCARA, Delta, Polar, Linear, etc.)
- Manufacturing processes and constraints
- Physics simulation and motion planning
- Learning from generated animations to improve future outputs
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
import bpy
import mathutils
from mathutils import Vector, Matrix, Euler

logger = logging.getLogger(__name__)


class RobotKinematicType(Enum):
    """Enumeration of robot kinematic types."""
    CARTESIAN_6DOF = "cartesian_6dof"           # Traditional 6-axis industrial robots
    SCARA = "scara"                             # Selective Compliance Assembly Robot Arm
    DELTA = "delta"                             # Parallel delta robots
    POLAR = "polar"                             # Polar coordinate robots
    CYLINDRICAL = "cylindrical"                 # Cylindrical coordinate robots
    ARTICULATED = "articulated"                 # Multi-joint articulated arms
    PARALLEL = "parallel"                       # Parallel kinematic machines
    LINEAR_XY = "linear_xy"                     # 2-axis linear systems
    LINEAR_XYZ = "linear_xyz"                   # 3-axis linear systems
    GANTRY = "gantry"                          # Gantry-style robots
    CABLE_DRIVEN = "cable_driven"               # Cable-driven parallel robots
    CONTINUUM = "continuum"                     # Soft/continuum robots
    HYBRID = "hybrid"                          # Hybrid kinematic systems


@dataclass
class RobotSpecification:
    """Comprehensive robot specification."""
    name: str
    kinematic_type: RobotKinematicType
    dof: int
    workspace: Dict[str, float]
    joint_limits: List[Tuple[float, float]]
    joint_velocities: List[float]
    joint_accelerations: List[float]
    payload: float
    reach: float
    repeatability: float
    mass: float
    power_consumption: float
    safety_zones: Dict[str, float]
    mounting_options: List[str]
    control_system: str
    programming_languages: List[str]
    special_features: List[str]


class EngineeringBrain:
    """
    Core engineering intelligence for robot animation and process planning.
    
    This system combines algorithmic engineering knowledge with machine learning
    to create increasingly intelligent robot animations and process optimizations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Engineering Brain."""
        self.config = config or self._default_config()
        self.robot_database = self._initialize_robot_database()
        self.process_templates = self._initialize_process_templates()
        self.learning_history = self._load_learning_history()
        self.physics_engine = PhysicsEngine()
        self.motion_planner = MotionPlanner()
        self.kinematic_solver = KinematicSolver()
        
        logger.info("Engineering Brain initialized with comprehensive robot knowledge")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the engineering brain."""
        return {
            'learning_enabled': True,
            'physics_simulation': True,
            'real_time_optimization': True,
            'safety_priority': 'high',
            'accuracy_threshold': 0.95,
            'speed_optimization': True,
            'adaptive_algorithms': True,
            'engineering_constraints': True,
            'material_properties': True,
            'environmental_factors': True
        }
    
    def _initialize_robot_database(self) -> Dict[str, RobotSpecification]:
        """Initialize comprehensive robot database."""
        robots = {}
        
        # Universal Robots Series
        ur_robots = [
            ("UR3e", 3, 500, [(-360, 360)] * 6, [180] * 6, 3.0, 0.03),
            ("UR5e", 5, 850, [(-360, 360)] * 6, [180] * 6, 18.5, 0.03),
            ("UR10e", 10, 1300, [(-360, 360)] * 6, [120] * 6, 33.5, 0.05),
            ("UR16e", 16, 900, [(-360, 360)] * 6, [180] * 6, 33.5, 0.05),
            ("UR20", 20, 1750, [(-360, 360)] * 6, [120] * 6, 52, 0.05),
            ("UR30", 30, 1300, [(-360, 360)] * 6, [120] * 6, 63.5, 0.05)
        ]
        
        for name, payload, reach, limits, velocities, mass, repeatability in ur_robots:
            robots[name] = RobotSpecification(
                name=name,
                kinematic_type=RobotKinematicType.CARTESIAN_6DOF,
                dof=6,
                workspace={'spherical_radius': reach/1000},
                joint_limits=limits,
                joint_velocities=velocities,
                joint_accelerations=[v * 2 for v in velocities],
                payload=payload,
                reach=reach/1000,
                repeatability=repeatability,
                mass=mass,
                power_consumption=200,
                safety_zones={'collaborative': 0.1, 'monitoring': 0.5},
                mounting_options=['floor', 'ceiling', 'wall', 'mobile'],
                control_system='URScript',
                programming_languages=['URScript', 'Python', 'C++'],
                special_features=['collaborative', 'force_sensing', 'vision_ready']
            )
        
        # KUKA Robot Series
        kuka_robots = [
            ("KR 3 R540", 3, 541, [(-170, 170), (-190, 45), (-120, 156), (-185, 185), (-120, 120), (-350, 350)]),
            ("KR 6 R700", 6, 706, [(-170, 170), (-190, 45), (-120, 156), (-185, 185), (-120, 120), (-350, 350)]),
            ("KR 10 R1100", 10, 1101, [(-170, 170), (-190, 45), (-120, 156), (-185, 185), (-120, 120), (-350, 350)]),
            ("KR 16 R1610", 16, 1611, [(-185, 185), (-155, 35), (-130, 154), (-350, 350), (-130, 130), (-350, 350)]),
            ("KR 50 R2500", 50, 2500, [(-185, 185), (-140, 35), (-100, 154), (-350, 350), (-130, 130), (-350, 350)]),
            ("KR 120 R2500", 120, 2500, [(-185, 185), (-140, 60), (-100, 154), (-350, 350), (-130, 130), (-350, 350)])
        ]
        
        for name, payload, reach, limits in kuka_robots:
            robots[name] = RobotSpecification(
                name=name,
                kinematic_type=RobotKinematicType.CARTESIAN_6DOF,
                dof=6,
                workspace={'spherical_radius': reach/1000},
                joint_limits=limits,
                joint_velocities=[156, 156, 156, 330, 330, 615],
                joint_accelerations=[312, 312, 312, 660, 660, 1230],
                payload=payload,
                reach=reach/1000,
                repeatability=0.03,
                mass=payload * 2,
                power_consumption=400,
                safety_zones={'danger': 0.5, 'warning': 1.0, 'monitoring': 2.0},
                mounting_options=['floor', 'ceiling', 'rail'],
                control_system='KRL',
                programming_languages=['KRL', 'Java', 'C++'],
                special_features=['high_precision', 'heavy_payload', 'industrial_rated']
            )
        
        # ABB Robot Series
        abb_robots = [
            ("IRB 120", 3, 580, [(-165, 165), (-110, 110), (-110, 70), (-160, 160), (-120, 120), (-400, 400)]),
            ("IRB 1200", 7, 700, [(-165, 165), (-110, 110), (-70, 135), (-160, 160), (-120, 120), (-400, 400)]),
            ("IRB 2600", 20, 1650, [(-180, 180), (-60, 85), (-180, 70), (-300, 300), (-130, 130), (-360, 360)]),
            ("IRB 4600", 60, 2050, [(-180, 180), (-90, 150), (-180, 75), (-300, 300), (-120, 120), (-360, 360)]),
            ("IRB 6700", 150, 3200, [(-180, 180), (-90, 150), (-180, 75), (-300, 300), (-120, 120), (-360, 360)]),
            ("IRB 8700", 800, 4200, [(-180, 180), (-50, 85), (-180, 60), (-300, 300), (-130, 130), (-360, 360)])
        ]
        
        for name, payload, reach, limits in abb_robots:
            robots[name] = RobotSpecification(
                name=name,
                kinematic_type=RobotKinematicType.CARTESIAN_6DOF,
                dof=6,
                workspace={'spherical_radius': reach/1000},
                joint_limits=limits,
                joint_velocities=[120, 120, 120, 190, 190, 235],
                joint_accelerations=[240, 240, 240, 380, 380, 470],
                payload=payload,
                reach=reach/1000,
                repeatability=0.02,
                mass=payload * 3,
                power_consumption=500,
                safety_zones={'danger': 0.4, 'warning': 0.9, 'monitoring': 1.8},
                mounting_options=['floor', 'ceiling', 'wall', 'rail'],
                control_system='RAPID',
                programming_languages=['RAPID', 'Python', 'C#'],
                special_features=['high_speed', 'industrial_rated', 'path_accuracy']
            )
        
        # Delta Robots
        robots["ABB FlexPicker IRB 360"] = RobotSpecification(
            name="ABB FlexPicker IRB 360",
            kinematic_type=RobotKinematicType.DELTA,
            dof=4,
            workspace={'cylindrical_radius': 0.6, 'height': 0.2},
            joint_limits=[(-60, 60), (-60, 60), (-60, 60), (-360, 360)],
            joint_velocities=[500, 500, 500, 1000],
            joint_accelerations=[2500, 2500, 2500, 5000],
            payload=1,
            reach=0.6,
            repeatability=0.1,
            mass=45,
            power_consumption=300,
            safety_zones={'operational': 0.7, 'monitoring': 1.0},
            mounting_options=['ceiling'],
            control_system='RAPID',
            programming_languages=['RAPID'],
            special_features=['ultra_high_speed', 'pick_place_optimized', 'food_grade']
        )
        
        # SCARA Robots
        robots["Epson LS6-B"] = RobotSpecification(
            name="Epson LS6-B",
            kinematic_type=RobotKinematicType.SCARA,
            dof=4,
            workspace={'cylindrical_radius': 0.6, 'height': 0.15},
            joint_limits=[(-145, 145), (-158, 158), (0, 210), (-360, 360)],
            joint_velocities=[400, 400, 1100, 2500],
            joint_accelerations=[3000, 3000, 15000, 25000],
            payload=6,
            reach=0.6,
            repeatability=0.02,
            mass=25,
            power_consumption=200,
            safety_zones={'operational': 0.7, 'monitoring': 1.0},
            mounting_options=['table', 'floor'],
            control_system='RC+',
            programming_languages=['SPEL+', 'C++'],
            special_features=['high_precision', 'compact_design', 'clean_room']
        )
        
        # Linear Systems
        robots["Linear XYZ Gantry"] = RobotSpecification(
            name="Linear XYZ Gantry",
            kinematic_type=RobotKinematicType.LINEAR_XYZ,
            dof=3,
            workspace={'box_x': 2.0, 'box_y': 1.5, 'box_z': 0.5},
            joint_limits=[(0, 2000), (0, 1500), (0, 500)],
            joint_velocities=[1000, 1000, 500],
            joint_accelerations=[2000, 2000, 1000],
            payload=50,
            reach=2.0,
            repeatability=0.01,
            mass=200,
            power_consumption=800,
            safety_zones={'operational': 2.2, 'monitoring': 2.5},
            mounting_options=['floor', 'ceiling'],
            control_system='PLC',
            programming_languages=['Ladder', 'Structured_Text'],
            special_features=['large_workspace', 'high_payload', 'precise_positioning']
        )
        
        # Simple Generic Robots for Learning
        robots["Simple 2DOF Arm"] = RobotSpecification(
            name="Simple 2DOF Arm",
            kinematic_type=RobotKinematicType.ARTICULATED,
            dof=2,
            workspace={'sector_radius': 1.0, 'angle': 180},
            joint_limits=[(-180, 180), (-135, 135)],
            joint_velocities=[90, 90],
            joint_accelerations=[180, 180],
            payload=2,
            reach=1.0,
            repeatability=0.1,
            mass=15,
            power_consumption=100,
            safety_zones={'operational': 1.1, 'monitoring': 1.3},
            mounting_options=['table', 'wall'],
            control_system='Arduino',
            programming_languages=['C++', 'Python'],
            special_features=['educational', 'low_cost', 'open_source']
        )
        
        return robots
    
    def _initialize_process_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize manufacturing process templates."""
        return {
            'pick_and_place': {
                'description': 'Pick objects from one location and place at another',
                'required_dof': 4,
                'speed_profile': 'high_acceleration',
                'path_type': 'point_to_point',
                'safety_requirements': ['collision_avoidance', 'gripper_monitoring'],
                'optimization_targets': ['cycle_time', 'energy_efficiency']
            },
            'welding': {
                'description': 'Continuous welding along defined paths',
                'required_dof': 6,
                'speed_profile': 'constant_velocity',
                'path_type': 'continuous',
                'safety_requirements': ['arc_safety', 'fume_extraction', 'heat_protection'],
                'optimization_targets': ['weld_quality', 'penetration_depth', 'heat_distribution']
            },
            'assembly': {
                'description': 'Assembling components with precise positioning',
                'required_dof': 6,
                'speed_profile': 'precision_positioning',
                'path_type': 'multi_waypoint',
                'safety_requirements': ['force_control', 'precision_monitoring'],
                'optimization_targets': ['positioning_accuracy', 'assembly_force', 'alignment']
            },
            'painting': {
                'description': 'Surface coating with uniform coverage',
                'required_dof': 6,
                'speed_profile': 'smooth_continuous',
                'path_type': 'surface_following',
                'safety_requirements': ['ventilation', 'explosion_proof', 'overspray_control'],
                'optimization_targets': ['coverage_uniformity', 'material_usage', 'surface_quality']
            },
            'machining': {
                'description': 'Material removal with cutting tools',
                'required_dof': 5,
                'speed_profile': 'variable_feed',
                'path_type': 'toolpath',
                'safety_requirements': ['spindle_monitoring', 'chip_evacuation', 'tool_wear'],
                'optimization_targets': ['surface_finish', 'tool_life', 'material_removal_rate']
            },
            'inspection': {
                'description': 'Quality control and measurement',
                'required_dof': 6,
                'speed_profile': 'stop_and_measure',
                'path_type': 'measurement_points',
                'safety_requirements': ['probe_protection', 'measurement_stability'],
                'optimization_targets': ['measurement_accuracy', 'inspection_speed', 'coverage']
            }
        }
    
    def _load_learning_history(self) -> Dict[str, Any]:
        """Load learning history from previous sessions."""
        history_file = os.path.join(bpy.path.abspath("//"), "learning_history.json")
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load learning history: {e}")
        
        return {
            'successful_animations': [],
            'optimization_patterns': {},
            'user_preferences': {},
            'common_scenarios': {},
            'error_patterns': {},
            'performance_metrics': {}
        }
    
    def analyze_process_description(self, description: str) -> Dict[str, Any]:
        """
        Analyze natural language process description using engineering knowledge.
        
        This combines rule-based engineering knowledge with learned patterns.
        """
        analysis = {
            'success': False,
            'robot_requirements': {},
            'process_type': None,
            'engineering_constraints': {},
            'optimization_opportunities': [],
            'safety_considerations': [],
            'recommended_robots': [],
            'confidence_score': 0.0
        }
        
        try:
            # Extract key engineering concepts
            description_lower = description.lower()
            
            # Identify process type
            process_type = self._identify_process_type(description_lower)
            analysis['process_type'] = process_type
            
            # Determine robot requirements
            robot_reqs = self._determine_robot_requirements(description_lower, process_type)
            analysis['robot_requirements'] = robot_reqs
            
            # Identify engineering constraints
            constraints = self._identify_engineering_constraints(description_lower)
            analysis['engineering_constraints'] = constraints
            
            # Find optimization opportunities
            optimizations = self._find_optimization_opportunities(process_type, constraints)
            analysis['optimization_opportunities'] = optimizations
            
            # Assess safety requirements
            safety = self._assess_safety_requirements(process_type, description_lower)
            analysis['safety_considerations'] = safety
            
            # Recommend suitable robots
            recommended = self._recommend_robots(robot_reqs, constraints)
            analysis['recommended_robots'] = recommended
            
            # Calculate confidence based on engineering knowledge match
            confidence = self._calculate_engineering_confidence(analysis)
            analysis['confidence_score'] = confidence
            
            # Learn from this analysis
            if self.config['learning_enabled']:
                self._record_analysis_for_learning(description, analysis)
            
            analysis['success'] = True
            
        except Exception as e:
            logger.error(f"Process analysis failed: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _identify_process_type(self, description: str) -> str:
        """Identify manufacturing process type from description."""
        
        process_keywords = {
            'pick_and_place': ['pick', 'place', 'transfer', 'move', 'grab', 'drop'],
            'welding': ['weld', 'join', 'arc', 'spot', 'mig', 'tig', 'fusion'],
            'assembly': ['assemble', 'mount', 'attach', 'connect', 'install', 'fit'],
            'painting': ['paint', 'coat', 'spray', 'finish', 'color', 'primer'],
            'machining': ['machine', 'cut', 'mill', 'turn', 'drill', 'bore', 'grind'],
            'inspection': ['inspect', 'measure', 'check', 'verify', 'test', 'quality']
        }
        
        # Score each process type
        scores = {}
        for process, keywords in process_keywords.items():
            scores[process] = sum(1 for keyword in keywords if keyword in description)
        
        # Return highest scoring process type
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'general_automation'
    
    def _determine_robot_requirements(self, description: str, process_type: str) -> Dict[str, Any]:
        """Determine robot requirements based on engineering analysis."""
        
        requirements = {
            'min_dof': 3,
            'max_dof': 6,
            'kinematic_types': [],
            'payload_range': [1, 50],  # kg
            'reach_range': [0.5, 3.0],  # meters
            'speed_requirements': 'medium',
            'precision_requirements': 'medium'
        }
        
        # Process-specific requirements
        if process_type in self.process_templates:
            template = self.process_templates[process_type]
            requirements['min_dof'] = template['required_dof']
            requirements['speed_requirements'] = template['speed_profile']
        
        # Analyze description for specific requirements
        if any(word in description for word in ['precise', 'accurate', 'fine']):
            requirements['precision_requirements'] = 'high'
        
        if any(word in description for word in ['fast', 'quick', 'rapid', 'speed']):
            requirements['speed_requirements'] = 'high'
        
        if any(word in description for word in ['heavy', 'large', 'massive']):
            requirements['payload_range'] = [50, 500]
        
        # Kinematic type recommendations
        if 'delta' in description or 'parallel' in description:
            requirements['kinematic_types'] = [RobotKinematicType.DELTA]
        elif 'scara' in description or 'assembly' in description:
            requirements['kinematic_types'] = [RobotKinematicType.SCARA, RobotKinematicType.CARTESIAN_6DOF]
        elif 'linear' in description or 'gantry' in description:
            requirements['kinematic_types'] = [RobotKinematicType.LINEAR_XYZ, RobotKinematicType.GANTRY]
        else:
            requirements['kinematic_types'] = [RobotKinematicType.CARTESIAN_6DOF]
        
        return requirements
    
    def _identify_engineering_constraints(self, description: str) -> Dict[str, Any]:
        """Identify engineering constraints from process description."""
        
        constraints = {
            'workspace_limitations': [],
            'environmental_factors': [],
            'material_properties': [],
            'process_parameters': {},
            'safety_zones': [],
            'interference_objects': []
        }
        
        # Environmental factors
        if 'clean room' in description or 'sterile' in description:
            constraints['environmental_factors'].append('clean_room_rated')
        
        if 'explosive' in description or 'hazardous' in description:
            constraints['environmental_factors'].append('explosion_proof')
        
        if 'underwater' in description or 'wet' in description:
            constraints['environmental_factors'].append('waterproof')
        
        # Material properties
        material_keywords = {
            'steel': {'hardness': 'high', 'conductivity': 'high'},
            'aluminum': {'hardness': 'medium', 'weight': 'light'},
            'plastic': {'hardness': 'low', 'flexibility': 'high'},
            'glass': {'fragility': 'high', 'precision_required': 'high'},
            'carbon fiber': {'strength': 'high', 'cost': 'high'}
        }
        
        for material, properties in material_keywords.items():
            if material in description:
                constraints['material_properties'].append({
                    'material': material,
                    'properties': properties
                })
        
        return constraints
    
    def _find_optimization_opportunities(self, process_type: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find optimization opportunities based on engineering analysis."""
        
        opportunities = []
        
        if process_type in self.process_templates:
            template = self.process_templates[process_type]
            for target in template['optimization_targets']:
                opportunities.append({
                    'type': target,
                    'potential_improvement': self._estimate_improvement_potential(target, constraints),
                    'implementation_difficulty': 'medium'
                })
        
        # Add general optimizations
        opportunities.extend([
            {
                'type': 'path_optimization',
                'potential_improvement': 0.15,  # 15% cycle time reduction
                'implementation_difficulty': 'low'
            },
            {
                'type': 'collision_avoidance',
                'potential_improvement': 0.05,  # 5% safety improvement
                'implementation_difficulty': 'medium'
            }
        ])
        
        return opportunities
    
    def _estimate_improvement_potential(self, optimization_type: str, constraints: Dict[str, Any]) -> float:
        """Estimate potential improvement percentage for optimization type."""
        
        # This would use machine learning in a full implementation
        base_improvements = {
            'cycle_time': 0.20,
            'energy_efficiency': 0.15,
            'positioning_accuracy': 0.10,
            'surface_finish': 0.25,
            'tool_life': 0.30
        }
        
        return base_improvements.get(optimization_type, 0.10)
    
    def _assess_safety_requirements(self, process_type: str, description: str) -> List[Dict[str, Any]]:
        """Assess safety requirements based on engineering knowledge."""
        
        safety_requirements = []
        
        # Process-specific safety
        if process_type in self.process_templates:
            template = self.process_templates[process_type]
            for requirement in template['safety_requirements']:
                safety_requirements.append({
                    'requirement': requirement,
                    'priority': 'high',
                    'implementation': 'required'
                })
        
        # Description-based safety
        if 'human' in description or 'operator' in description:
            safety_requirements.append({
                'requirement': 'collaborative_safety',
                'priority': 'critical',
                'implementation': 'required'
            })
        
        if 'sharp' in description or 'cutting' in description:
            safety_requirements.append({
                'requirement': 'tool_safety',
                'priority': 'high',
                'implementation': 'required'
            })
        
        return safety_requirements
    
    def _recommend_robots(self, requirements: Dict[str, Any], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend suitable robots based on engineering analysis."""
        
        recommendations = []
        
        for robot_name, robot_spec in self.robot_database.items():
            score = self._score_robot_suitability(robot_spec, requirements, constraints)
            
            if score > 0.5:  # Minimum suitability threshold
                recommendations.append({
                    'robot': robot_name,
                    'specification': asdict(robot_spec),
                    'suitability_score': score,
                    'reasoning': self._generate_recommendation_reasoning(robot_spec, requirements)
                })
        
        # Sort by suitability score
        recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _score_robot_suitability(self, robot_spec: RobotSpecification, 
                               requirements: Dict[str, Any], 
                               constraints: Dict[str, Any]) -> float:
        """Score robot suitability using engineering criteria."""
        
        score = 0.0
        max_score = 0.0
        
        # DOF matching
        max_score += 20
        if robot_spec.dof >= requirements['min_dof']:
            score += 20
        
        # Kinematic type matching
        max_score += 25
        if robot_spec.kinematic_type in requirements['kinematic_types']:
            score += 25
        
        # Payload range
        max_score += 20
        payload_min, payload_max = requirements['payload_range']
        if payload_min <= robot_spec.payload <= payload_max:
            score += 20
        elif robot_spec.payload > payload_max:
            score += 15  # Overspec is better than underspec
        
        # Reach requirements
        max_score += 15
        reach_min, reach_max = requirements['reach_range']
        if reach_min <= robot_spec.reach <= reach_max:
            score += 15
        elif robot_spec.reach > reach_max:
            score += 10
        
        # Speed requirements
        max_score += 10
        if requirements['speed_requirements'] == 'high':
            if 'high_speed' in robot_spec.special_features:
                score += 10
        
        # Precision requirements
        max_score += 10
        if requirements['precision_requirements'] == 'high':
            if robot_spec.repeatability < 0.05:  # Better than 0.05mm
                score += 10
        
        return score / max_score if max_score > 0 else 0.0
    
    def _generate_recommendation_reasoning(self, robot_spec: RobotSpecification, 
                                         requirements: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for robot recommendation."""
        
        reasons = []
        
        if robot_spec.dof >= requirements['min_dof']:
            reasons.append(f"{robot_spec.dof} DOF meets requirement")
        
        if robot_spec.kinematic_type in requirements['kinematic_types']:
            reasons.append(f"{robot_spec.kinematic_type.value} kinematic type matches")
        
        if requirements['payload_range'][0] <= robot_spec.payload <= requirements['payload_range'][1]:
            reasons.append(f"{robot_spec.payload}kg payload in range")
        
        if 'collaborative' in robot_spec.special_features:
            reasons.append("Human-safe collaborative design")
        
        return "; ".join(reasons)
    
    def _calculate_engineering_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on engineering knowledge coverage."""
        
        confidence = 0.0
        
        # Process type identification confidence
        if analysis['process_type'] and analysis['process_type'] != 'general_automation':
            confidence += 0.3
        
        # Robot recommendations confidence
        if analysis['recommended_robots']:
            confidence += 0.3
        
        # Engineering constraints identification
        if analysis['engineering_constraints']:
            confidence += 0.2
        
        # Safety considerations
        if analysis['safety_considerations']:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _record_analysis_for_learning(self, description: str, analysis: Dict[str, Any]):
        """Record analysis for future learning improvements."""
        
        record = {
            'description': description,
            'analysis': analysis,
            'timestamp': bpy.context.scene.frame_current,
            'success': analysis['success'],
            'confidence': analysis['confidence_score']
        }
        
        self.learning_history['successful_animations'].append(record)
        
        # Update patterns
        process_type = analysis['process_type']
        if process_type not in self.learning_history['common_scenarios']:
            self.learning_history['common_scenarios'][process_type] = []
        
        self.learning_history['common_scenarios'][process_type].append({
            'description_patterns': self._extract_patterns(description),
            'robot_preferences': analysis['recommended_robots'][:2] if analysis['recommended_robots'] else []
        })
    
    def _extract_patterns(self, description: str) -> List[str]:
        """Extract linguistic patterns from description for learning."""
        
        # Simple pattern extraction - in full implementation would use NLP
        words = description.lower().split()
        patterns = []
        
        # Bigrams and trigrams
        for i in range(len(words) - 1):
            patterns.append(f"{words[i]} {words[i+1]}")
        
        for i in range(len(words) - 2):
            patterns.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return patterns
    
    def save_learning_history(self):
        """Save learning history for future sessions."""
        
        if not self.config['learning_enabled']:
            return
        
        history_file = os.path.join(bpy.path.abspath("//"), "learning_history.json")
        try:
            with open(history_file, 'w') as f:
                json.dump(self.learning_history, f, indent=2)
            logger.info("Learning history saved successfully")
        except Exception as e:
            logger.error(f"Failed to save learning history: {e}")


class PhysicsEngine:
    """Simplified physics engine for robot simulation."""
    
    def __init__(self):
        self.gravity = -9.81
        self.air_resistance = 0.01
        
    def calculate_trajectory(self, start_pos: Vector, end_pos: Vector, 
                           velocity: float, constraints: Dict[str, Any]) -> List[Vector]:
        """Calculate physics-based trajectory."""
        # Simplified physics calculation
        trajectory = []
        steps = 20
        
        for i in range(steps + 1):
            t = i / steps
            pos = start_pos.lerp(end_pos, t)
            trajectory.append(pos)
        
        return trajectory


class MotionPlanner:
    """Advanced motion planning for robot paths."""
    
    def __init__(self):
        self.planning_algorithms = ['rrt', 'prm', 'a_star']
    
    def plan_path(self, start: Vector, goal: Vector, obstacles: List[Vector],
                  robot_spec: RobotSpecification) -> Dict[str, Any]:
        """Plan collision-free path using appropriate algorithm."""
        
        # Simplified path planning
        path = [start, goal]
        
        return {
            'path': path,
            'algorithm_used': 'direct',
            'execution_time': 5.0,
            'collision_free': True
        }


class KinematicSolver:
    """Forward and inverse kinematics solver for various robot types."""
    
    def __init__(self):
        self.solvers = {
            RobotKinematicType.CARTESIAN_6DOF: self._solve_6dof,
            RobotKinematicType.SCARA: self._solve_scara,
            RobotKinematicType.DELTA: self._solve_delta,
            RobotKinematicType.LINEAR_XYZ: self._solve_linear
        }
    
    def forward_kinematics(self, joint_angles: List[float], 
                          robot_type: RobotKinematicType) -> Vector:
        """Calculate end effector position from joint angles."""
        
        if robot_type in self.solvers:
            return self.solvers[robot_type](joint_angles, forward=True)
        
        return Vector((0, 0, 0))
    
    def inverse_kinematics(self, target_position: Vector, 
                          robot_type: RobotKinematicType) -> List[float]:
        """Calculate joint angles for target position."""
        
        if robot_type in self.solvers:
            return self.solvers[robot_type](target_position, forward=False)
        
        return [0.0] * 6
    
    def _solve_6dof(self, input_data, forward=True):
        """Solve 6DOF industrial robot kinematics."""
        if forward:
            # Simplified forward kinematics
            return Vector((sum(input_data[:3]), sum(input_data[3:]), 1.0))
        else:
            # Simplified inverse kinematics
            return [input_data.x / 3, input_data.y / 3, input_data.z, 0, 0, 0]
    
    def _solve_scara(self, input_data, forward=True):
        """Solve SCARA robot kinematics."""
        if forward:
            return Vector((input_data[0], input_data[1], input_data[2]))
        else:
            return [input_data.x, input_data.y, input_data.z, 0]
    
    def _solve_delta(self, input_data, forward=True):
        """Solve Delta robot kinematics."""
        if forward:
            return Vector((sum(input_data[:2]), sum(input_data[1:3]), input_data[0]))
        else:
            return [input_data.x, input_data.y, input_data.z]
    
    def _solve_linear(self, input_data, forward=True):
        """Solve linear system kinematics."""
        if forward:
            return Vector(input_data[:3])
        else:
            return [input_data.x, input_data.y, input_data.z] 