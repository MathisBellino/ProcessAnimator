#!/usr/bin/env python3
"""
Robot Analyzer for ProcessAnimator

Automatically analyzes robot models to determine reach, degrees of freedom,
movement constraints, and safety zones. Provides intelligent path planning
and collision detection.
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
import bpy
import bmesh
import mathutils
from mathutils import Vector, Euler, Matrix

logger = logging.getLogger(__name__)


class RobotAnalyzer:
    """
    Intelligent robot analysis system.
    
    Automatically detects robot specifications, constraints, and capabilities
    from Blender armature/mesh data to enable smart animation planning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RobotAnalyzer.
        
        Args:
            config: Optional configuration for robot analysis
        """
        self.config = config or self._default_config()
        self.robot_database = self._load_robot_database()
        self.analyzed_robots = {}
        
        logger.info("RobotAnalyzer initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration for robot analysis."""
        return {
            'safety_margin': 0.1,  # meters
            'collision_buffer': 0.05,  # meters
            'max_reach_samples': 100,
            'joint_limit_safety_factor': 0.95,
            'velocity_limit_factor': 0.8,
            'enable_dynamic_safety': True,
            'workspace_visualization': True,
            'constraint_visualization': True
        }
    
    def _load_robot_database(self) -> Dict[str, Dict[str, Any]]:
        """Load database of known robot specifications."""
        return {
            'ABB_IRB6700': {
                'dof': 6,
                'reach': 3.2,  # meters
                'payload': 150,  # kg
                'joint_limits': [
                    (-180, 180),   # Base
                    (-90, 150),    # Shoulder
                    (-180, 75),    # Elbow
                    (-180, 180),   # Wrist 1
                    (-120, 120),   # Wrist 2
                    (-360, 360)    # Wrist 3
                ],
                'joint_velocities': [120, 120, 120, 190, 190, 235],  # deg/s
                'safety_zones': {
                    'danger_zone': 0.5,
                    'warning_zone': 1.0,
                    'monitoring_zone': 2.0
                }
            },
            'KUKA_KR16': {
                'dof': 6,
                'reach': 1.611,
                'payload': 16,
                'joint_limits': [
                    (-185, 185),
                    (-155, 35),
                    (-130, 154),
                    (-350, 350),
                    (-130, 130),
                    (-350, 350)
                ],
                'joint_velocities': [156, 156, 156, 330, 330, 615],
                'safety_zones': {
                    'danger_zone': 0.3,
                    'warning_zone': 0.8,
                    'monitoring_zone': 1.5
                }
            },
            'UR10': {
                'dof': 6,
                'reach': 1.3,
                'payload': 10,
                'joint_limits': [
                    (-360, 360),
                    (-360, 360),
                    (-360, 360),
                    (-360, 360),
                    (-360, 360),
                    (-360, 360)
                ],
                'joint_velocities': [120, 120, 180, 180, 180, 180],
                'safety_zones': {
                    'danger_zone': 0.2,  # Collaborative robot
                    'warning_zone': 0.5,
                    'monitoring_zone': 1.0
                },
                'collaborative': True
            },
            'FANUC_M20': {
                'dof': 6,
                'reach': 1.811,
                'payload': 20,
                'joint_limits': [
                    (-180, 180),
                    (-130, 145),
                    (-210, 265),
                    (-200, 200),
                    (-135, 135),
                    (-360, 360)
                ],
                'joint_velocities': [230, 195, 250, 430, 430, 630],
                'safety_zones': {
                    'danger_zone': 0.4,
                    'warning_zone': 0.9,
                    'monitoring_zone': 1.8
                }
            }
        }
    
    def analyze_robot(self, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """
        Analyze robot object to determine specifications and constraints.
        
        Args:
            robot_object: Blender object representing the robot
            
        Returns:
            Dictionary containing complete robot analysis
        """
        try:
            if not robot_object:
                return {'success': False, 'error': 'No robot object provided'}
            
            # Detect robot type
            robot_type = self._detect_robot_type(robot_object)
            
            # Get base specifications
            base_specs = self._get_base_specifications(robot_type, robot_object)
            
            # Analyze geometry
            geometry_analysis = self._analyze_robot_geometry(robot_object)
            
            # Analyze kinematics
            kinematic_analysis = self._analyze_kinematics(robot_object)
            
            # Calculate workspace
            workspace_analysis = self._calculate_workspace(robot_object, base_specs)
            
            # Detect constraints
            constraints_analysis = self._detect_constraints(robot_object)
            
            # Calculate safety zones
            safety_analysis = self._calculate_safety_zones(robot_object, base_specs)
            
            # Compile analysis results
            analysis = {
                'success': True,
                'robot_name': robot_object.name,
                'robot_type': robot_type,
                'base_specifications': base_specs,
                'geometry': geometry_analysis,
                'kinematics': kinematic_analysis,
                'workspace': workspace_analysis,
                'constraints': constraints_analysis,
                'safety': safety_analysis,
                'analysis_timestamp': bpy.context.scene.frame_current
            }
            
            # Cache analysis
            self.analyzed_robots[robot_object.name] = analysis
            
            logger.info(f"Analyzed robot: {robot_type}")
            return analysis
            
        except Exception as e:
            logger.error(f"Robot analysis failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _detect_robot_type(self, robot_object: bpy.types.Object) -> str:
        """Detect robot type from object name and properties."""
        
        obj_name = robot_object.name.upper()
        
        # Check against known robot patterns
        robot_patterns = {
            'ABB_IRB6700': ['ABB', 'IRB', '6700'],
            'KUKA_KR16': ['KUKA', 'KR', '16'],
            'UR10': ['UR', '10', 'UNIVERSAL'],
            'FANUC_M20': ['FANUC', 'M20', 'M-20']
        }
        
        for robot_type, patterns in robot_patterns.items():
            if all(pattern in obj_name for pattern in patterns):
                return robot_type
        
        # Check custom properties
        if 'robot_type' in robot_object.keys():
            return robot_object['robot_type']
        
        # Fallback: analyze geometry to guess type
        return self._guess_robot_type_from_geometry(robot_object)
    
    def _guess_robot_type_from_geometry(self, robot_object: bpy.types.Object) -> str:
        """Guess robot type from geometric analysis."""
        
        # Simple heuristic based on bounding box
        if robot_object.type == 'MESH':
            bbox = robot_object.bound_box
            max_dimension = max(
                max(corner[0] for corner in bbox) - min(corner[0] for corner in bbox),
                max(corner[1] for corner in bbox) - min(corner[1] for corner in bbox),
                max(corner[2] for corner in bbox) - min(corner[2] for corner in bbox)
            )
            
            if max_dimension > 3.0:
                return 'ABB_IRB6700'  # Large industrial robot
            elif max_dimension > 1.5:
                return 'FANUC_M20'    # Medium industrial robot
            else:
                return 'UR10'         # Collaborative robot
        
        return 'GENERIC_6DOF'
    
    def _get_base_specifications(self, robot_type: str, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """Get base specifications for the robot."""
        
        # Start with database specs
        base_specs = self.robot_database.get(robot_type, {
            'dof': 6,
            'reach': 1.0,
            'payload': 10,
            'joint_limits': [(-180, 180)] * 6,
            'joint_velocities': [100] * 6,
            'safety_zones': {'danger_zone': 0.3, 'warning_zone': 0.8, 'monitoring_zone': 1.5}
        }).copy()
        
        # Override with custom properties if present
        for prop in ['dof', 'reach', 'payload']:
            if prop in robot_object.keys():
                base_specs[prop] = robot_object[prop]
        
        return base_specs
    
    def _analyze_robot_geometry(self, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """Analyze robot geometric properties."""
        
        geometry = {
            'object_type': robot_object.type,
            'base_position': list(robot_object.location),
            'base_rotation': list(robot_object.rotation_euler),
            'scale': list(robot_object.scale)
        }
        
        if robot_object.type == 'MESH':
            # Analyze mesh geometry
            mesh = robot_object.data
            geometry.update({
                'vertex_count': len(mesh.vertices),
                'face_count': len(mesh.polygons),
                'bounding_box': [list(corner) for corner in robot_object.bound_box],
                'center_of_mass': list(robot_object.bound_box[0])  # Simplified
            })
        
        elif robot_object.type == 'ARMATURE':
            # Analyze armature
            armature = robot_object.data
            geometry.update({
                'bone_count': len(armature.bones),
                'bones': [bone.name for bone in armature.bones],
                'bone_hierarchy': self._get_bone_hierarchy(armature)
            })
        
        return geometry
    
    def _get_bone_hierarchy(self, armature: bpy.types.Armature) -> Dict[str, Any]:
        """Get bone hierarchy for armature analysis."""
        hierarchy = {}
        
        for bone in armature.bones:
            hierarchy[bone.name] = {
                'parent': bone.parent.name if bone.parent else None,
                'children': [child.name for child in bone.children],
                'length': bone.length,
                'head': list(bone.head),
                'tail': list(bone.tail)
            }
        
        return hierarchy
    
    def _analyze_kinematics(self, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """Analyze robot kinematics and joint configuration."""
        
        kinematics = {
            'joint_configuration': 'unknown',
            'degrees_of_freedom': 6,
            'joint_types': [],
            'kinematic_chain': []
        }
        
        if robot_object.type == 'ARMATURE':
            armature = robot_object.data
            
            # Analyze joint types from bone constraints
            for bone in armature.bones:
                if bone.parent:
                    joint_type = self._determine_joint_type(bone)
                    kinematics['joint_types'].append({
                        'bone': bone.name,
                        'type': joint_type,
                        'axis': self._get_primary_rotation_axis(bone)
                    })
            
            # Build kinematic chain
            kinematics['kinematic_chain'] = self._build_kinematic_chain(armature)
        
        return kinematics
    
    def _determine_joint_type(self, bone: bpy.types.Bone) -> str:
        """Determine joint type from bone properties."""
        
        # Simple heuristic based on bone name and orientation
        bone_name = bone.name.lower()
        
        if 'base' in bone_name or 'root' in bone_name:
            return 'revolute'  # Base rotation
        elif 'shoulder' in bone_name:
            return 'revolute'
        elif 'elbow' in bone_name:
            return 'revolute'
        elif 'wrist' in bone_name:
            return 'revolute'
        else:
            return 'revolute'  # Default assumption
    
    def _get_primary_rotation_axis(self, bone: bpy.types.Bone) -> str:
        """Get primary rotation axis for bone."""
        
        # Simplified: use bone direction to determine axis
        bone_vector = bone.tail - bone.head
        
        # Find dominant axis
        abs_x, abs_y, abs_z = abs(bone_vector.x), abs(bone_vector.y), abs(bone_vector.z)
        
        if abs_z > abs_x and abs_z > abs_y:
            return 'Z'
        elif abs_y > abs_x:
            return 'Y'
        else:
            return 'X'
    
    def _build_kinematic_chain(self, armature: bpy.types.Armature) -> List[Dict[str, Any]]:
        """Build kinematic chain representation."""
        
        chain = []
        root_bones = [bone for bone in armature.bones if not bone.parent]
        
        for root_bone in root_bones:
            self._traverse_kinematic_chain(root_bone, chain, 0)
        
        return chain
    
    def _traverse_kinematic_chain(self, bone: bpy.types.Bone, chain: List[Dict[str, Any]], depth: int):
        """Recursively traverse kinematic chain."""
        
        chain.append({
            'name': bone.name,
            'depth': depth,
            'length': bone.length,
            'position': list(bone.head),
            'orientation': list(bone.tail - bone.head)
        })
        
        for child in bone.children:
            self._traverse_kinematic_chain(child, chain, depth + 1)
    
    def _calculate_workspace(self, robot_object: bpy.types.Object, base_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate robot workspace and reachable area."""
        
        reach = base_specs.get('reach', 1.0)
        base_position = Vector(robot_object.location)
        
        # Calculate workspace boundaries
        workspace = {
            'base_position': list(base_position),
            'max_reach': reach,
            'workspace_type': 'spherical',  # Simplified assumption
            'reachable_volume': (4/3) * math.pi * (reach ** 3),
            'workspace_bounds': {
                'x_min': base_position.x - reach,
                'x_max': base_position.x + reach,
                'y_min': base_position.y - reach,
                'y_max': base_position.y + reach,
                'z_min': max(0, base_position.z - reach),  # Don't go below ground
                'z_max': base_position.z + reach
            }
        }
        
        # Sample reachable points
        workspace['sample_points'] = self._sample_workspace_points(base_position, reach)
        
        return workspace
    
    def _sample_workspace_points(self, base_position: Vector, reach: float) -> List[List[float]]:
        """Sample points within the robot workspace."""
        
        sample_points = []
        num_samples = self.config['max_reach_samples']
        
        for i in range(num_samples):
            # Generate random point within sphere
            theta = 2 * math.pi * (i / num_samples)
            phi = math.acos(1 - 2 * ((i * 0.618) % 1))  # Golden ratio sampling
            r = reach * (0.5 + 0.5 * ((i * 0.382) % 1))  # Vary radius
            
            x = base_position.x + r * math.sin(phi) * math.cos(theta)
            y = base_position.y + r * math.sin(phi) * math.sin(theta)
            z = base_position.z + r * math.cos(phi)
            
            # Only include points above ground
            if z >= 0:
                sample_points.append([x, y, z])
        
        return sample_points
    
    def _detect_constraints(self, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """Detect movement constraints and limitations."""
        
        constraints = {
            'joint_limits': [],
            'collision_objects': [],
            'workspace_limitations': [],
            'safety_constraints': []
        }
        
        # Detect collision objects in scene
        for obj in bpy.context.scene.objects:
            if obj != robot_object and obj.type == 'MESH':
                distance = (obj.location - robot_object.location).length
                if distance < 5.0:  # Within potential collision range
                    constraints['collision_objects'].append({
                        'name': obj.name,
                        'position': list(obj.location),
                        'distance': distance,
                        'bounding_box': [list(corner) for corner in obj.bound_box]
                    })
        
        # Detect workspace limitations
        constraints['workspace_limitations'] = self._detect_workspace_limitations(robot_object)
        
        return constraints
    
    def _detect_workspace_limitations(self, robot_object: bpy.types.Object) -> List[Dict[str, Any]]:
        """Detect workspace limitations from scene geometry."""
        
        limitations = []
        
        # Check for ground plane
        if robot_object.location.z > 0:
            limitations.append({
                'type': 'ground_plane',
                'description': 'Cannot move below ground level',
                'constraint_plane': [0, 0, 1, 0]  # Z = 0 plane
            })
        
        # Check for walls or boundaries
        for obj in bpy.context.scene.objects:
            if 'wall' in obj.name.lower() or 'boundary' in obj.name.lower():
                limitations.append({
                    'type': 'boundary',
                    'object': obj.name,
                    'position': list(obj.location)
                })
        
        return limitations
    
    def _calculate_safety_zones(self, robot_object: bpy.types.Object, base_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate safety zones around the robot."""
        
        base_position = Vector(robot_object.location)
        safety_zones = base_specs.get('safety_zones', {})
        
        # Apply safety margin from config
        safety_margin = self.config['safety_margin']
        
        zones = {}
        for zone_name, zone_radius in safety_zones.items():
            adjusted_radius = zone_radius + safety_margin
            zones[zone_name] = {
                'radius': adjusted_radius,
                'center': list(base_position),
                'volume': (4/3) * math.pi * (adjusted_radius ** 3),
                'boundary_points': self._generate_zone_boundary(base_position, adjusted_radius)
            }
        
        return {
            'zones': zones,
            'safety_margin': safety_margin,
            'collaborative_robot': base_specs.get('collaborative', False)
        }
    
    def _generate_zone_boundary(self, center: Vector, radius: float) -> List[List[float]]:
        """Generate boundary points for safety zone visualization."""
        
        boundary_points = []
        num_points = 32
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            z = center.z
            
            boundary_points.append([x, y, z])
        
        return boundary_points
    
    def check_collision(self, robot_object: bpy.types.Object, target_position: Vector) -> Dict[str, Any]:
        """Check for potential collisions with target position."""
        
        analysis = self.analyzed_robots.get(robot_object.name)
        if not analysis:
            analysis = self.analyze_robot(robot_object)
        
        collision_result = {
            'collision_detected': False,
            'collision_objects': [],
            'safety_violations': [],
            'recommendations': []
        }
        
        # Check against known collision objects
        collision_buffer = self.config['collision_buffer']
        
        for constraint in analysis['constraints']['collision_objects']:
            obj_position = Vector(constraint['position'])
            distance = (target_position - obj_position).length
            
            if distance < collision_buffer:
                collision_result['collision_detected'] = True
                collision_result['collision_objects'].append(constraint['name'])
        
        # Check safety zone violations
        safety_zones = analysis['safety']['zones']
        for zone_name, zone_data in safety_zones.items():
            zone_center = Vector(zone_data['center'])
            zone_radius = zone_data['radius']
            distance = (target_position - zone_center).length
            
            if distance < zone_radius and zone_name == 'danger_zone':
                collision_result['safety_violations'].append({
                    'zone': zone_name,
                    'violation_distance': zone_radius - distance
                })
        
        # Generate recommendations
        if collision_result['collision_detected']:
            collision_result['recommendations'].append("Adjust target position to avoid collisions")
        
        if collision_result['safety_violations']:
            collision_result['recommendations'].append("Move target outside safety zones")
        
        return collision_result
    
    def visualize_analysis(self, robot_object: bpy.types.Object) -> Dict[str, Any]:
        """Create visualization of robot analysis."""
        
        analysis = self.analyzed_robots.get(robot_object.name)
        if not analysis:
            return {'success': False, 'error': 'Robot not analyzed'}
        
        visualization_objects = []
        
        try:
            # Visualize workspace
            if self.config['workspace_visualization']:
                workspace_vis = self._create_workspace_visualization(analysis['workspace'])
                visualization_objects.extend(workspace_vis)
            
            # Visualize safety zones
            safety_vis = self._create_safety_visualization(analysis['safety'])
            visualization_objects.extend(safety_vis)
            
            # Visualize constraints
            if self.config['constraint_visualization']:
                constraint_vis = self._create_constraint_visualization(analysis['constraints'])
                visualization_objects.extend(constraint_vis)
            
            return {
                'success': True,
                'visualization_objects': visualization_objects
            }
            
        except Exception as e:
            logger.error(f"Visualization failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_workspace_visualization(self, workspace: Dict[str, Any]) -> List[str]:
        """Create workspace visualization objects."""
        
        # Create workspace boundary sphere
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=workspace['max_reach'],
            location=workspace['base_position']
        )
        
        workspace_sphere = bpy.context.active_object
        workspace_sphere.name = "Workspace_Boundary"
        
        # Make it wireframe and transparent
        material = bpy.data.materials.new(name="Workspace_Material")
        material.use_nodes = True
        material.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2  # Alpha
        workspace_sphere.data.materials.append(material)
        
        return [workspace_sphere.name]
    
    def _create_safety_visualization(self, safety: Dict[str, Any]) -> List[str]:
        """Create safety zone visualization objects."""
        
        visualization_objects = []
        
        zone_colors = {
            'danger_zone': (1.0, 0.0, 0.0, 0.3),    # Red
            'warning_zone': (1.0, 1.0, 0.0, 0.2),   # Yellow
            'monitoring_zone': (0.0, 1.0, 0.0, 0.1) # Green
        }
        
        for zone_name, zone_data in safety['zones'].items():
            # Create zone sphere
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=zone_data['radius'],
                location=zone_data['center']
            )
            
            zone_sphere = bpy.context.active_object
            zone_sphere.name = f"Safety_{zone_name}"
            
            # Apply zone color
            if zone_name in zone_colors:
                material = bpy.data.materials.new(name=f"Safety_{zone_name}_Material")
                material.use_nodes = True
                material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = zone_colors[zone_name]
                material.node_tree.nodes["Principled BSDF"].inputs[21].default_value = zone_colors[zone_name][3]
                zone_sphere.data.materials.append(material)
            
            visualization_objects.append(zone_sphere.name)
        
        return visualization_objects
    
    def _create_constraint_visualization(self, constraints: Dict[str, Any]) -> List[str]:
        """Create constraint visualization objects."""
        
        visualization_objects = []
        
        # Visualize collision objects with warning colors
        for collision_obj in constraints['collision_objects']:
            # Create warning marker
            bpy.ops.mesh.primitive_cube_add(
                size=0.1,
                location=collision_obj['position']
            )
            
            marker = bpy.context.active_object
            marker.name = f"Collision_Warning_{collision_obj['name']}"
            
            # Make it red and prominent
            material = bpy.data.materials.new(name="Collision_Warning_Material")
            material.use_nodes = True
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
            marker.data.materials.append(material)
            
            visualization_objects.append(marker.name)
        
        return visualization_objects 