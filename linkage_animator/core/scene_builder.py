#!/usr/bin/env python3
"""
Scene Builder for Robot Animation Studio

Automatically constructs complete robot animation scenes with:
- Robot placement and setup
- Part positioning and constraints
- Environment creation
- Interactive animation systems
- Teaching coordinate capture
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Euler
from typing import Dict, List, Any, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class SceneBuilder:
    """
    Automatic scene builder for robot animation environments.
    
    Creates complete scenes with robots, parts, environments, and
    interactive systems for animation and teaching.
    """
    
    def __init__(self):
        self.scene_components = {}
        self.interactive_objects = []
        self.teaching_points = []
        self.animation_keyframes = []
        
        logger.info("Scene Builder initialized")
    
    def build_complete_scene(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete robot animation scene based on AI configuration.
        
        Args:
            config: Configuration from AI parameter assistant
            
        Returns:
            Dictionary containing build results and component references
        """
        try:
            # Clear existing scene (optional)
            if config.get('clear_scene', False):
                self._clear_scene()
            
            # 1. Create environment
            environment_result = self._create_environment(config)
            
            # 2. Import and position robot
            robot_result = self._setup_robot(config)
            
            # 3. Create target objects/parts
            parts_result = self._create_target_parts(config)
            
            # 4. Setup interactive systems
            interactive_result = self._setup_interactive_systems(config)
            
            # 5. Create animation framework
            animation_result = self._setup_animation_framework(config)
            
            # 6. Configure lighting and camera
            visual_result = self._setup_scene_visuals(config)
            
            # Collect all results
            build_result = {
                'success': True,
                'components': {
                    'environment': environment_result,
                    'robot': robot_result,
                    'parts': parts_result,
                    'interactive': interactive_result,
                    'animation': animation_result,
                    'visuals': visual_result
                },
                'scene_objects': self.scene_components,
                'interactive_objects': self.interactive_objects,
                'message': f"Scene built successfully for {config['task_type']} task"
            }
            
            logger.info(f"Scene building completed: {config['task_type']}")
            return build_result
            
        except Exception as e:
            logger.error(f"Scene building failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to build scene: {str(e)}"
            }
    
    def _clear_scene(self):
        """Clear existing scene objects (optional)."""
        # Select all mesh objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Delete default objects except camera and light
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.name in ['Cube']:
                obj.select_set(True)
                bpy.data.objects.remove(obj, do_unlink=True)
    
    def _create_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create appropriate environment for the task."""
        task_type = config['task_type']
        
        # Create floor/workbench
        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = "Workbench"
        
        # Apply material based on task
        self._apply_environment_material(floor, task_type)
        
        # Create work area boundaries
        boundaries = self._create_work_boundaries(task_type)
        
        # Add task-specific environment elements
        task_elements = self._create_task_specific_environment(config)
        
        environment_objects = [floor] + boundaries + task_elements
        self.scene_components['environment'] = environment_objects
        
        return {
            'success': True,
            'objects': environment_objects,
            'main_surface': floor,
            'work_area': boundaries
        }
    
    def _apply_environment_material(self, obj, task_type: str):
        """Apply appropriate material to environment objects."""
        material_configs = {
            'welding': {'color': (0.3, 0.3, 0.3, 1.0), 'metallic': 0.8, 'roughness': 0.2},
            'assembly': {'color': (0.8, 0.8, 0.9, 1.0), 'metallic': 0.1, 'roughness': 0.7},
            'pick_and_place': {'color': (0.7, 0.8, 0.7, 1.0), 'metallic': 0.0, 'roughness': 0.8}
        }
        
        config = material_configs.get(task_type, material_configs['assembly'])
        
        # Create material
        mat_name = f"Environment_{task_type}"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            
            if mat.node_tree:
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    principled.inputs['Base Color'].default_value = config['color']
                    principled.inputs['Metallic'].default_value = config['metallic']
                    principled.inputs['Roughness'].default_value = config['roughness']
        
        # Apply material
        material = bpy.data.materials[mat_name]
        if not obj.data.materials:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
    
    def _create_work_boundaries(self, task_type: str) -> List:
        """Create work area boundaries and safety zones."""
        boundaries = []
        
        # Create invisible collision boundaries
        bpy.ops.mesh.primitive_cube_add(size=8, location=(0, 0, 2))
        boundary_box = bpy.context.active_object
        boundary_box.name = "Work_Boundary"
        boundary_box.display_type = 'WIRE'
        boundary_box.hide_render = True
        
        boundaries.append(boundary_box)
        
        return boundaries
    
    def _create_task_specific_environment(self, config: Dict[str, Any]) -> List:
        """Create task-specific environment elements."""
        task_type = config['task_type']
        elements = []
        
        if task_type == 'welding':
            # Create welding table and fixtures
            elements.extend(self._create_welding_environment())
        elif task_type == 'assembly':
            # Create assembly stations and part bins
            elements.extend(self._create_assembly_environment())
        elif task_type == 'pick_and_place':
            # Create conveyors and storage areas
            elements.extend(self._create_pick_place_environment())
        
        return elements
    
    def _create_welding_environment(self) -> List:
        """Create welding-specific environment."""
        elements = []
        
        # Welding fixture
        bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 1))
        fixture = bpy.context.active_object
        fixture.name = "Welding_Fixture"
        elements.append(fixture)
        
        return elements
    
    def _create_assembly_environment(self) -> List:
        """Create assembly-specific environment."""
        elements = []
        
        # Part bins
        for i in range(3):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(i*2-2, 3, 0.5))
            bin_obj = bpy.context.active_object
            bin_obj.name = f"Part_Bin_{i+1}"
            elements.append(bin_obj)
        
        return elements
    
    def _create_pick_place_environment(self) -> List:
        """Create pick-and-place specific environment."""
        elements = []
        
        # Conveyor belt (simple)
        bpy.ops.mesh.primitive_cube_add(scale=(4, 0.5, 0.1), location=(0, -3, 0.1))
        conveyor = bpy.context.active_object
        conveyor.name = "Conveyor_Belt"
        elements.append(conveyor)
        
        return elements
    
    def _setup_robot(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Import and setup robot based on configuration."""
        from .robot_catalogue import robot_catalogue
        
        # Determine robot to use
        robot_id = self._select_robot_for_task(config)
        
        # Import robot
        import_result = robot_catalogue.import_robot_to_scene(robot_id)
        
        if not import_result['success']:
            # Fallback: create simple robot placeholder
            robot_objects = self._create_robot_placeholder(config)
            robot_info = {'name': 'Placeholder Robot', 'type': 'Generic'}
        else:
            robot_objects = import_result['objects']
            robot_info = import_result['robot_info']
        
        # Position robot appropriately
        if robot_objects:
            main_robot = robot_objects[0]
            main_robot.location = self._calculate_robot_position(config)
            
            # Setup robot for interaction
            self._setup_robot_interaction(robot_objects, config)
        
        self.scene_components['robot'] = robot_objects
        
        return {
            'success': True,
            'objects': robot_objects,
            'robot_info': robot_info,
            'main_object': robot_objects[0] if robot_objects else None
        }
    
    def _select_robot_for_task(self, config: Dict[str, Any]) -> str:
        """Select appropriate robot for the task."""
        task_type = config['task_type']
        
        robot_selection = {
            'pick_and_place': 'ur5e',
            'welding': 'kuka_kr10',
            'assembly': 'abb_irb120'
        }
        
        return robot_selection.get(task_type, 'ur5e')
    
    def _create_robot_placeholder(self, config: Dict[str, Any]) -> List:
        """Create a placeholder robot if import fails."""
        # Create simple robot representation
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
        base = bpy.context.active_object
        base.name = "Robot_Base"
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=2, location=(0, 0, 2))
        arm = bpy.context.active_object
        arm.name = "Robot_Arm"
        
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0, 0, 3.2))
        gripper = bpy.context.active_object
        gripper.name = "Robot_Gripper"
        
        return [base, arm, gripper]
    
    def _calculate_robot_position(self, config: Dict[str, Any]) -> Vector:
        """Calculate optimal robot position for the task."""
        task_type = config['task_type']
        
        positions = {
            'welding': Vector((-2, 0, 0)),
            'assembly': Vector((0, -2, 0)),
            'pick_and_place': Vector((2, 0, 0))
        }
        
        return positions.get(task_type, Vector((0, 0, 0)))
    
    def _setup_robot_interaction(self, robot_objects: List, config: Dict[str, Any]):
        """Setup robot for interactive animation."""
        if not robot_objects:
            return
        
        main_robot = robot_objects[0]
        
        # Add custom properties for interaction
        main_robot['interactive'] = True
        main_robot['task_type'] = config['task_type']
        main_robot['can_drag'] = True
        
        # Setup constraints for realistic movement
        self._add_robot_constraints(robot_objects)
    
    def _add_robot_constraints(self, robot_objects: List):
        """Add constraints to robot for realistic movement."""
        # Add basic constraints to prevent unrealistic positions
        for obj in robot_objects:
            if obj.name.endswith('_arm') or obj.name.endswith('_gripper'):
                # Add limit location constraint
                limit_constraint = obj.constraints.new(type='LIMIT_LOCATION')
                limit_constraint.use_limit_x = True
                limit_constraint.min_x = -5
                limit_constraint.max_x = 5
                limit_constraint.use_limit_y = True
                limit_constraint.min_y = -5
                limit_constraint.max_y = 5
                limit_constraint.use_limit_z = True
                limit_constraint.min_z = 0.1
                limit_constraint.max_z = 6
    
    def _create_target_parts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create target objects/parts for the animation."""
        task_type = config['task_type']
        target_object = config.get('target_object', 'part')
        
        parts = []
        
        # Create parts based on task type
        if task_type == 'pick_and_place':
            parts.extend(self._create_pick_place_parts(target_object, config))
        elif task_type == 'welding':
            parts.extend(self._create_welding_parts(config))
        elif task_type == 'assembly':
            parts.extend(self._create_assembly_parts(config))
        
        # Setup parts for interaction
        for part in parts:
            self._setup_part_interaction(part, config)
        
        self.scene_components['parts'] = parts
        
        return {
            'success': True,
            'objects': parts,
            'count': len(parts)
        }
    
    def _create_pick_place_parts(self, target_object: str, config: Dict[str, Any]) -> List:
        """Create parts for pick and place operations."""
        parts = []
        quantity = config.get('repetitions', 3)
        
        for i in range(min(quantity, 5)):  # Limit to 5 parts
            # Create part based on target object description
            if 'electronic' in target_object.lower():
                bpy.ops.mesh.primitive_cube_add(scale=(0.3, 0.2, 0.1), location=(i*0.5-1, -3, 0.2))
            elif 'screw' in target_object.lower():
                bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(i*0.3-0.6, -3, 0.25))
            else:
                bpy.ops.mesh.primitive_cube_add(scale=(0.4, 0.4, 0.3), location=(i*0.6-1.2, -3, 0.3))
            
            part = bpy.context.active_object
            part.name = f"{target_object}_{i+1}"
            parts.append(part)
        
        return parts
    
    def _create_welding_parts(self, config: Dict[str, Any]) -> List:
        """Create parts for welding operations."""
        parts = []
        
        # Create metal plates to weld
        bpy.ops.mesh.primitive_cube_add(scale=(1, 0.1, 0.5), location=(3, -0.6, 1))
        plate1 = bpy.context.active_object
        plate1.name = "Metal_Plate_1"
        parts.append(plate1)
        
        bpy.ops.mesh.primitive_cube_add(scale=(1, 0.1, 0.5), location=(3, 0.6, 1))
        plate2 = bpy.context.active_object
        plate2.name = "Metal_Plate_2"
        parts.append(plate2)
        
        return parts
    
    def _create_assembly_parts(self, config: Dict[str, Any]) -> List:
        """Create parts for assembly operations."""
        parts = []
        
        # Create base part
        bpy.ops.mesh.primitive_cube_add(scale=(0.8, 0.8, 0.2), location=(0, 0, 0.2))
        base_part = bpy.context.active_object
        base_part.name = "Assembly_Base"
        parts.append(base_part)
        
        # Create components to assemble
        for i in range(2):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.4, location=((i-0.5)*2, 3, 0.4))
            component = bpy.context.active_object
            component.name = f"Component_{i+1}"
            parts.append(component)
        
        return parts
    
    def _setup_part_interaction(self, part, config: Dict[str, Any]):
        """Setup part for interactive manipulation."""
        # Add custom properties
        part['interactive'] = True
        part['can_drag'] = True
        part['target_part'] = True
        part['task_type'] = config['task_type']
        
        # Add to interactive objects list
        self.interactive_objects.append(part)
        
        # Add visual feedback material
        self._add_interactive_material(part)
    
    def _add_interactive_material(self, obj):
        """Add material that highlights interactive objects."""
        mat_name = "Interactive_Material"
        
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            
            if mat.node_tree:
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    principled.inputs['Base Color'].default_value = (0.3, 0.7, 1.0, 1.0)  # Light blue
                    principled.inputs['Emission'].default_value = (0.1, 0.3, 0.5, 1.0)
                    principled.inputs['Emission Strength'].default_value = 0.3
        
        # Apply material
        material = bpy.data.materials[mat_name]
        if not obj.data.materials:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
    
    def _setup_interactive_systems(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup interactive animation and teaching systems."""
        
        # Create teaching point system
        teaching_result = self._setup_teaching_system(config)
        
        # Create drag and drop system
        drag_result = self._setup_drag_drop_system(config)
        
        # Create coordinate capture system
        coordinate_result = self._setup_coordinate_capture(config)
        
        return {
            'success': True,
            'teaching_system': teaching_result,
            'drag_drop': drag_result,
            'coordinate_capture': coordinate_result
        }
    
    def _setup_teaching_system(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup system for teaching robot positions."""
        
        # Create teaching points collection
        teaching_collection = bpy.data.collections.new("Teaching_Points")
        bpy.context.scene.collection.children.link(teaching_collection)
        
        # Create initial teaching points based on task
        initial_points = self._create_initial_teaching_points(config)
        
        for point in initial_points:
            teaching_collection.objects.link(point)
            bpy.context.scene.collection.objects.unlink(point)
        
        return {
            'success': True,
            'collection': teaching_collection,
            'points': initial_points
        }
    
    def _create_initial_teaching_points(self, config: Dict[str, Any]) -> List:
        """Create initial teaching points for the task."""
        points = []
        task_type = config['task_type']
        
        # Create point markers
        point_locations = self._get_task_teaching_points(task_type)
        
        for i, location in enumerate(point_locations):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=location)
            point = bpy.context.active_object
            point.name = f"Teaching_Point_{i+1}"
            
            # Make point interactive
            point['teaching_point'] = True
            point['point_id'] = i+1
            point['can_drag'] = True
            
            # Add distinctive material
            self._add_teaching_point_material(point)
            
            points.append(point)
            self.teaching_points.append({
                'object': point,
                'location': location,
                'point_id': i+1
            })
        
        return points
    
    def _get_task_teaching_points(self, task_type: str) -> List[Vector]:
        """Get default teaching point locations for task type."""
        points = {
            'pick_and_place': [
                Vector((0, -3, 2)),  # Pick position
                Vector((0, 0, 3)),   # Intermediate
                Vector((0, 3, 2)),   # Place position
            ],
            'welding': [
                Vector((3, -0.6, 1.5)),  # Start weld
                Vector((3, 0, 1.5)),     # Mid weld
                Vector((3, 0.6, 1.5)),   # End weld
            ],
            'assembly': [
                Vector((0, 3, 2)),    # Pick component
                Vector((0, 1, 3)),    # Approach
                Vector((0, 0, 1)),    # Assembly position
            ]
        }
        
        return points.get(task_type, [Vector((0, 0, 2))])
    
    def _add_teaching_point_material(self, obj):
        """Add distinctive material for teaching points."""
        mat_name = "Teaching_Point_Material"
        
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            
            if mat.node_tree:
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    principled.inputs['Base Color'].default_value = (1.0, 0.3, 0.3, 1.0)  # Red
                    principled.inputs['Emission'].default_value = (0.5, 0.1, 0.1, 1.0)
                    principled.inputs['Emission Strength'].default_value = 0.5
        
        # Apply material
        material = bpy.data.materials[mat_name]
        if not obj.data.materials:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
    
    def _setup_drag_drop_system(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup drag and drop interaction system."""
        
        # Add custom properties to scene for drag/drop state
        scene = bpy.context.scene
        scene['drag_drop_enabled'] = True
        scene['drag_mode'] = False
        scene['selected_object'] = ""
        
        return {
            'success': True,
            'enabled': True,
            'interactive_count': len(self.interactive_objects)
        }
    
    def _setup_coordinate_capture(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup system for capturing coordinates during teaching."""
        
        # Create coordinate capture collection
        coord_collection = bpy.data.collections.new("Captured_Coordinates")
        bpy.context.scene.collection.children.link(coord_collection)
        
        # Setup coordinate tracking
        scene = bpy.context.scene
        scene['coordinate_capture_enabled'] = True
        scene['captured_coordinates'] = []
        
        return {
            'success': True,
            'collection': coord_collection,
            'capture_enabled': True
        }
    
    def _setup_animation_framework(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup animation framework and keyframe system."""
        
        # Set scene frame rate and duration
        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = int(config['animation']['duration'] * config['animation']['frame_rate'])
        scene.frame_current = 1
        
        # Setup animation properties
        scene['animation_config'] = config['animation']
        scene['keyframe_mode'] = True
        scene['auto_keyframe'] = config.get('auto_keyframe', True)
        
        # Create animation markers for key positions
        markers = self._create_animation_markers(config)
        
        return {
            'success': True,
            'frame_range': (scene.frame_start, scene.frame_end),
            'markers': markers,
            'duration': config['animation']['duration']
        }
    
    def _create_animation_markers(self, config: Dict[str, Any]) -> List:
        """Create timeline markers for animation phases."""
        markers = []
        duration = config['animation']['duration']
        frame_rate = config['animation']['frame_rate']
        
        # Create markers for different phases
        phase_markers = [
            ('Start', 1),
            ('Pick/Approach', int(duration * 0.25 * frame_rate)),
            ('Action', int(duration * 0.5 * frame_rate)),
            ('Return', int(duration * 0.75 * frame_rate)),
            ('End', int(duration * frame_rate))
        ]
        
        for name, frame in phase_markers:
            marker = bpy.context.scene.timeline_markers.new(name, frame=frame)
            markers.append(marker)
        
        return markers
    
    def _setup_scene_visuals(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup lighting, camera, and visual elements."""
        
        # Setup lighting
        lighting_result = self._setup_lighting(config)
        
        # Setup camera
        camera_result = self._setup_camera(config)
        
        # Setup visual aids
        visual_aids_result = self._setup_visual_aids(config)
        
        return {
            'success': True,
            'lighting': lighting_result,
            'camera': camera_result,
            'visual_aids': visual_aids_result
        }
    
    def _setup_lighting(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup appropriate lighting for the scene."""
        
        # Add area light for better illumination
        bpy.ops.object.light_add(type='AREA', location=(2, 2, 4))
        area_light = bpy.context.active_object
        area_light.name = "Area_Light"
        area_light.data.energy = 100
        area_light.data.size = 2
        
        # Add fill light
        bpy.ops.object.light_add(type='AREA', location=(-2, -2, 3))
        fill_light = bpy.context.active_object
        fill_light.name = "Fill_Light"
        fill_light.data.energy = 50
        fill_light.data.size = 3
        
        return {
            'success': True,
            'lights': [area_light, fill_light]
        }
    
    def _setup_camera(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup camera for optimal viewing."""
        
        # Position camera for good view of workspace
        camera = bpy.context.scene.camera
        if camera:
            camera.location = Vector((7, -7, 5))
            camera.rotation_euler = Euler((1.1, 0, 0.785), 'XYZ')
            
            # Setup camera for animation
            camera.data.lens = 35  # Wide angle for workspace view
            
        return {
            'success': True,
            'camera': camera,
            'positioned': True
        }
    
    def _setup_visual_aids(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup visual aids for animation (paths, coordinates, etc.)."""
        aids = []
        
        if config['visualization']['show_path']:
            # Create path visualization
            path_aid = self._create_path_visualization(config)
            if path_aid:
                aids.append(path_aid)
        
        if config['visualization']['show_coordinates']:
            # Create coordinate display
            coord_aid = self._create_coordinate_display(config)
            if coord_aid:
                aids.append(coord_aid)
        
        return {
            'success': True,
            'aids': aids,
            'count': len(aids)
        }
    
    def _create_path_visualization(self, config: Dict[str, Any]) -> Optional:
        """Create path visualization curve."""
        # Create a curve for motion path
        curve_data = bpy.data.curves.new('Motion_Path', type='CURVE')
        curve_data.dimensions = '3D'
        
        # Add spline
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(2)  # Total of 3 points
        
        # Set points based on teaching points
        if self.teaching_points:
            for i, point_data in enumerate(self.teaching_points[:3]):
                if i < len(spline.bezier_points):
                    spline.bezier_points[i].co = point_data['location']
                    spline.bezier_points[i].handle_left = point_data['location']
                    spline.bezier_points[i].handle_right = point_data['location']
        
        # Create object
        curve_obj = bpy.data.objects.new('Motion_Path', curve_data)
        bpy.context.scene.collection.objects.link(curve_obj)
        
        # Set curve properties
        curve_data.bevel_depth = 0.02
        curve_data.use_fill_caps = True
        
        return curve_obj
    
    def _create_coordinate_display(self, config: Dict[str, Any]) -> Optional:
        """Create coordinate display system."""
        # For now, return None - this would be implemented with custom drawing
        # or text objects showing coordinates
        return None


# Blender Operators for Scene Building
class ROBOTANIM_OT_build_ai_scene(bpy.types.Operator):
    """Build complete scene from AI configuration"""
    bl_idname = "robotanim.build_ai_scene"
    bl_label = "Build AI Scene"
    bl_description = "Build complete robot animation scene from AI configuration"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get AI configuration
        config = context.scene.get('ai_animation_config')
        if not config:
            self.report({'ERROR'}, "No AI configuration found. Please run AI assistant first.")
            return {'CANCELLED'}
        
        # Initialize scene builder
        scene_builder = SceneBuilder()
        
        # Build scene
        result = scene_builder.build_complete_scene(config)
        
        if result['success']:
            self.report({'INFO'}, result['message'])
            
            # Store scene components for later use
            context.scene['scene_components'] = result['scene_objects']
            context.scene['interactive_objects'] = [obj.name for obj in result['interactive_objects']]
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result['message'])
            return {'CANCELLED'}


class ROBOTANIM_OT_toggle_drag_mode(bpy.types.Operator):
    """Toggle drag and drop mode for interactive teaching"""
    bl_idname = "robotanim.toggle_drag_mode"
    bl_label = "Toggle Drag Mode"
    bl_description = "Enable/disable drag and drop mode for robot teaching"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        current_state = scene.get('drag_mode', False)
        scene['drag_mode'] = not current_state
        
        if scene['drag_mode']:
            self.report({'INFO'}, "Drag mode enabled - click and drag interactive objects to teach positions")
        else:
            self.report({'INFO'}, "Drag mode disabled")
        
        return {'FINISHED'}


class ROBOTANIM_OT_capture_coordinate(bpy.types.Operator):
    """Capture current coordinate for teaching"""
    bl_idname = "robotanim.capture_coordinate"
    bl_label = "Capture Coordinate"
    bl_description = "Capture current position as teaching coordinate"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No object selected to capture coordinate from")
            return {'CANCELLED'}
        
        # Capture coordinate
        coord = active_obj.location.copy()
        
        # Store in scene
        captured_coords = context.scene.get('captured_coordinates', [])
        captured_coords.append({
            'object': active_obj.name,
            'location': list(coord),
            'frame': context.scene.frame_current
        })
        context.scene['captured_coordinates'] = captured_coords
        
        self.report({'INFO'}, f"Captured coordinate: {coord.x:.2f}, {coord.y:.2f}, {coord.z:.2f}")
        return {'FINISHED'}


# Registration
scene_builder_classes = [
    ROBOTANIM_OT_build_ai_scene,
    ROBOTANIM_OT_toggle_drag_mode,
    ROBOTANIM_OT_capture_coordinate,
]


def register_scene_builder():
    """Register scene builder classes."""
    for cls in scene_builder_classes:
        bpy.utils.register_class(cls)


def unregister_scene_builder():
    """Unregister scene builder classes."""
    for cls in reversed(scene_builder_classes):
        bpy.utils.unregister_class(cls) 