#!/usr/bin/env python3
"""
Smart Dashboard UI for ProcessAnimator

Advanced UI system that provides:
- Real-time process visualization as you type
- Modal interfaces for complex operations
- Progressive quality rendering (wireframe → full render)
- Smart workflow guidance
- Learning-enhanced suggestions
"""

import logging
import bpy
import bmesh
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from bpy.types import Panel, Operator, PropertyGroup, WorkSpaceTool
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
import mathutils
from mathutils import Vector, Matrix
from typing import Dict, Any, List, Optional
import time
import threading

from ..core.engineering_brain import EngineeringBrain, RobotKinematicType
from ..process_animator import ProcessAnimator

logger = logging.getLogger(__name__)


class SmartDashboard:
    """
    Advanced smart dashboard for ProcessAnimator.
    
    Provides real-time visualization, modal interfaces, and intelligent
    workflow guidance based on engineering knowledge and learning.
    """
    
    def __init__(self):
        self.engineering_brain = EngineeringBrain()
        self.process_animator = ProcessAnimator()
        self.is_active = False
        self.current_mode = 'dashboard'
        self.real_time_preview = None
        self.modal_operator = None
        self.visualization_cache = {}
        self.ui_state = self._initialize_ui_state()
        
        # Real-time analysis
        self.last_analysis_time = 0
        self.analysis_delay = 0.5  # seconds
        self.current_analysis = None
        
        logger.info("Smart Dashboard initialized")
    
    def _initialize_ui_state(self) -> Dict[str, Any]:
        """Initialize UI state management."""
        return {
            'current_description': '',
            'analysis_results': None,
            'selected_robot': None,
            'visualization_mode': 'wireframe',
            'quality_level': 'preview',
            'show_engineering_details': False,
            'auto_optimize': True,
            'learning_suggestions': [],
            'workflow_step': 0,
            'modal_stack': []
        }
    
    def activate_dashboard(self):
        """Activate the smart dashboard interface."""
        self.is_active = True
        self.current_mode = 'dashboard'
        
        # Register real-time handlers
        if self._real_time_handler not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(self._real_time_handler)
        
        # Setup viewport overlay
        self._setup_viewport_overlay()
        
        logger.info("Smart Dashboard activated")
    
    def deactivate_dashboard(self):
        """Deactivate the smart dashboard interface."""
        self.is_active = False
        
        # Unregister handlers
        if self._real_time_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(self._real_time_handler)
        
        # Cleanup viewport overlay
        self._cleanup_viewport_overlay()
        
        logger.info("Smart Dashboard deactivated")
    
    def _real_time_handler(self, scene, depsgraph):
        """Handle real-time updates for live preview."""
        if not self.is_active:
            return
        
        current_time = time.time()
        if current_time - self.last_analysis_time > self.analysis_delay:
            self._update_real_time_analysis()
            self.last_analysis_time = current_time
    
    def _update_real_time_analysis(self):
        """Update real-time analysis based on current description."""
        
        # Get current description from UI
        if hasattr(bpy.context.scene, 'process_animator_props'):
            props = bpy.context.scene.process_animator_props
            description = props.process_description
            
            if description != self.ui_state['current_description']:
                self.ui_state['current_description'] = description
                
                # Perform analysis in background thread
                if description.strip():
                    threading.Thread(
                        target=self._background_analysis,
                        args=(description,),
                        daemon=True
                    ).start()
    
    def _background_analysis(self, description: str):
        """Perform engineering analysis in background thread."""
        try:
            analysis = self.engineering_brain.analyze_process_description(description)
            
            # Update UI state (thread-safe)
            bpy.app.timers.register(
                lambda: self._update_analysis_results(analysis),
                first_interval=0.01
            )
            
        except Exception as e:
            logger.error(f"Background analysis failed: {e}")
    
    def _update_analysis_results(self, analysis: Dict[str, Any]):
        """Update analysis results in main thread."""
        self.ui_state['analysis_results'] = analysis
        self.current_analysis = analysis
        
        # Update visualization
        self._update_real_time_visualization()
        
        # Generate learning suggestions
        self._generate_learning_suggestions()
        
        # Force UI redraw
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    
    def _update_real_time_visualization(self):
        """Update real-time visualization based on analysis."""
        if not self.current_analysis or not self.current_analysis['success']:
            return
        
        try:
            # Create/update robot visualization
            self._visualize_recommended_robots()
            
            # Create/update process visualization
            self._visualize_process_flow()
            
            # Create/update safety zones
            self._visualize_safety_zones()
            
            # Update engineering constraints
            self._visualize_constraints()
            
        except Exception as e:
            logger.error(f"Visualization update failed: {e}")
    
    def _visualize_recommended_robots(self):
        """Visualize recommended robots in real-time."""
        if not self.current_analysis['recommended_robots']:
            return
        
        # Get top recommendation
        top_robot = self.current_analysis['recommended_robots'][0]
        robot_spec = top_robot['specification']
        
        # Create or update robot placeholder
        robot_name = f"Preview_{robot_spec['name']}"
        
        if robot_name not in bpy.data.objects:
            self._create_robot_placeholder(robot_name, robot_spec)
        else:
            self._update_robot_placeholder(robot_name, robot_spec)
    
    def _create_robot_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create robot placeholder visualization."""
        
        # Create based on kinematic type
        kinematic_type = spec['kinematic_type']
        
        if kinematic_type == 'cartesian_6dof':
            self._create_6dof_placeholder(name, spec)
        elif kinematic_type == 'scara':
            self._create_scara_placeholder(name, spec)
        elif kinematic_type == 'delta':
            self._create_delta_placeholder(name, spec)
        elif kinematic_type == 'linear_xyz':
            self._create_linear_placeholder(name, spec)
        else:
            self._create_generic_placeholder(name, spec)
    
    def _create_6dof_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create 6DOF robot placeholder."""
        
        # Create base
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.2, depth=0.3, location=(0, 0, 0.15)
        )
        base = bpy.context.active_object
        base.name = f"{name}_base"
        
        # Create arm segments
        reach = spec['reach']
        segment_length = reach / 3
        
        for i in range(3):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.05, depth=segment_length,
                location=(0, 0, 0.3 + i * segment_length)
            )
            segment = bpy.context.active_object
            segment.name = f"{name}_segment_{i}"
            segment.rotation_euler = (1.57, 0, 0)  # Rotate to point outward
        
        # Group objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.name.startswith(name):
                obj.select_set(True)
        
        bpy.ops.object.join()
        robot = bpy.context.active_object
        robot.name = name
        
        # Apply preview material
        self._apply_preview_material(robot, (0.2, 0.5, 0.8, 0.7))
    
    def _create_scara_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create SCARA robot placeholder."""
        
        # Create base
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.15, depth=0.2, location=(0, 0, 0.1)
        )
        base = bpy.context.active_object
        base.name = f"{name}_base"
        
        # Create horizontal arms
        reach = spec['reach']
        arm1_length = reach * 0.6
        arm2_length = reach * 0.4
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.03, depth=arm1_length,
            location=(arm1_length/2, 0, 0.2)
        )
        arm1 = bpy.context.active_object
        arm1.name = f"{name}_arm1"
        arm1.rotation_euler = (0, 1.57, 0)
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.02, depth=arm2_length,
            location=(arm1_length + arm2_length/2, 0, 0.2)
        )
        arm2 = bpy.context.active_object
        arm2.name = f"{name}_arm2"
        arm2.rotation_euler = (0, 1.57, 0)
        
        # Group and apply material
        bpy.ops.object.select_all(action='DESELECT')
        for obj in [base, arm1, arm2]:
            obj.select_set(True)
        
        bpy.ops.object.join()
        robot = bpy.context.active_object
        robot.name = name
        
        self._apply_preview_material(robot, (0.8, 0.5, 0.2, 0.7))
    
    def _create_delta_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create Delta robot placeholder."""
        
        # Create top platform
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3, depth=0.05, location=(0, 0, 1.5)
        )
        platform = bpy.context.active_object
        platform.name = f"{name}_platform"
        
        # Create three arms
        for i in range(3):
            angle = i * 2.09  # 120 degrees
            x = 0.25 * math.cos(angle)
            y = 0.25 * math.sin(angle)
            
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.02, depth=0.8,
                location=(x, y, 1.1)
            )
            arm = bpy.context.active_object
            arm.name = f"{name}_arm_{i}"
        
        # Create end effector
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.05, depth=0.1, location=(0, 0, 0.5)
        )
        effector = bpy.context.active_object
        effector.name = f"{name}_effector"
        
        # Group and apply material
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.name.startswith(name):
                obj.select_set(True)
        
        bpy.ops.object.join()
        robot = bpy.context.active_object
        robot.name = name
        
        self._apply_preview_material(robot, (0.5, 0.8, 0.2, 0.7))
    
    def _create_linear_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create linear system placeholder."""
        
        workspace = spec['workspace']
        x_size = workspace.get('box_x', 2.0)
        y_size = workspace.get('box_y', 1.5)
        z_size = workspace.get('box_z', 0.5)
        
        # Create gantry frame
        bpy.ops.mesh.primitive_cube_add(
            size=1, location=(x_size/2, y_size/2, z_size/2)
        )
        frame = bpy.context.active_object
        frame.scale = (x_size, y_size, z_size)
        frame.name = f"{name}_frame"
        
        # Make it wireframe-like
        frame.display_type = 'WIRE'
        
        # Create moving carriage
        bpy.ops.mesh.primitive_cube_add(
            size=0.2, location=(x_size/4, y_size/4, z_size/2)
        )
        carriage = bpy.context.active_object
        carriage.name = f"{name}_carriage"
        
        self._apply_preview_material(carriage, (0.8, 0.2, 0.5, 0.7))
    
    def _create_generic_placeholder(self, name: str, spec: Dict[str, Any]):
        """Create generic robot placeholder."""
        
        bpy.ops.mesh.primitive_monkey_add(size=0.5, location=(0, 0, 0.5))
        robot = bpy.context.active_object
        robot.name = name
        
        self._apply_preview_material(robot, (0.5, 0.5, 0.5, 0.7))
    
    def _apply_preview_material(self, obj: bpy.types.Object, color: tuple):
        """Apply preview material to object."""
        
        # Create material
        mat_name = f"Preview_Material_{obj.name}"
        if mat_name in bpy.data.materials:
            material = bpy.data.materials[mat_name]
        else:
            material = bpy.data.materials.new(name=mat_name)
            material.use_nodes = True
            
            # Setup nodes
            nodes = material.node_tree.nodes
            nodes.clear()
            
            # Output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            
            # Emission shader for glow effect
            emission = nodes.new(type='ShaderNodeEmission')
            emission.inputs[0].default_value = color[:3] + (1.0,)
            emission.inputs[1].default_value = 0.5  # Strength
            
            # Mix with transparency
            transparent = nodes.new(type='ShaderNodeBsdfTransparent')
            mix = nodes.new(type='ShaderNodeMixShader')
            mix.inputs[0].default_value = color[3]  # Alpha
            
            # Connect nodes
            links = material.node_tree.links
            links.new(transparent.outputs[0], mix.inputs[1])
            links.new(emission.outputs[0], mix.inputs[2])
            links.new(mix.outputs[0], output.inputs[0])
        
        # Apply material
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
        
        # Enable transparency
        material.blend_method = 'BLEND'
    
    def _visualize_process_flow(self):
        """Visualize the manufacturing process flow."""
        if not self.current_analysis['process_type']:
            return
        
        process_type = self.current_analysis['process_type']
        
        # Create process flow visualization based on type
        if process_type == 'pick_and_place':
            self._create_pick_place_flow()
        elif process_type == 'welding':
            self._create_welding_flow()
        elif process_type == 'assembly':
            self._create_assembly_flow()
        # Add more process types as needed
    
    def _create_pick_place_flow(self):
        """Create pick and place flow visualization."""
        
        # Create pick location
        if "PickLocation" not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add(size=0.1, location=(1, 1, 0.5))
            pick = bpy.context.active_object
            pick.name = "PickLocation"
            self._apply_preview_material(pick, (0, 1, 0, 0.5))
        
        # Create place location
        if "PlaceLocation" not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-1, -1, 0.5))
            place = bpy.context.active_object
            place.name = "PlaceLocation"
            self._apply_preview_material(place, (1, 0, 0, 0.5))
        
        # Create path visualization
        self._create_path_visualization(
            Vector((1, 1, 0.5)), Vector((-1, -1, 0.5)), "PickPlacePath"
        )
    
    def _create_welding_flow(self):
        """Create welding flow visualization."""
        
        # Create weld seam
        if "WeldSeam" not in bpy.data.objects:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.01, depth=1.0, location=(0, 0, 0.5)
            )
            seam = bpy.context.active_object
            seam.name = "WeldSeam"
            seam.rotation_euler = (0, 1.57, 0)
            self._apply_preview_material(seam, (1, 0.5, 0, 0.8))
    
    def _create_assembly_flow(self):
        """Create assembly flow visualization."""
        
        # Create assembly components
        components = [
            ("Component1", (0.5, 0.5, 0.3)),
            ("Component2", (-0.5, 0.5, 0.3)),
            ("Component3", (0, -0.5, 0.3))
        ]
        
        for name, location in components:
            if name not in bpy.data.objects:
                bpy.ops.mesh.primitive_cube_add(size=0.2, location=location)
                comp = bpy.context.active_object
                comp.name = name
                self._apply_preview_material(comp, (0.3, 0.3, 0.8, 0.6))
    
    def _create_path_visualization(self, start: Vector, end: Vector, name: str):
        """Create path visualization between two points."""
        
        if name in bpy.data.objects:
            return
        
        # Create curve
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 2
        
        # Create spline
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(1)  # Already has one point, add one more
        
        # Set points
        polyline.points[0].co = (start.x, start.y, start.z, 1)
        polyline.points[1].co = (end.x, end.y, end.z, 1)
        
        # Create object
        curve_obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(curve_obj)
        
        # Style as path
        curve_data.bevel_depth = 0.01
        self._apply_preview_material(curve_obj, (1, 1, 0, 0.7))
    
    def _visualize_safety_zones(self):
        """Visualize safety zones around robots."""
        if not self.current_analysis['recommended_robots']:
            return
        
        top_robot = self.current_analysis['recommended_robots'][0]
        safety_zones = top_robot['specification']['safety_zones']
        
        for zone_name, radius in safety_zones.items():
            zone_obj_name = f"SafetyZone_{zone_name}"
            
            if zone_obj_name not in bpy.data.objects:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0, 0, 0.5))
                zone = bpy.context.active_object
                zone.name = zone_obj_name
                zone.display_type = 'WIRE'
                
                # Color code safety zones
                colors = {
                    'danger': (1, 0, 0, 0.3),
                    'warning': (1, 1, 0, 0.2),
                    'monitoring': (0, 1, 0, 0.1),
                    'collaborative': (0, 0, 1, 0.2),
                    'operational': (0.5, 0.5, 1, 0.2)
                }
                
                color = colors.get(zone_name, (0.5, 0.5, 0.5, 0.2))
                self._apply_preview_material(zone, color)
    
    def _visualize_constraints(self):
        """Visualize engineering constraints."""
        constraints = self.current_analysis.get('engineering_constraints', {})
        
        # Visualize workspace limitations
        for limitation in constraints.get('workspace_limitations', []):
            if limitation['type'] == 'ground_plane':
                self._create_ground_plane()
    
    def _create_ground_plane(self):
        """Create ground plane constraint visualization."""
        if "GroundPlane" not in bpy.data.objects:
            bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
            ground = bpy.context.active_object
            ground.name = "GroundPlane"
            ground.display_type = 'WIRE'
            self._apply_preview_material(ground, (0.3, 0.3, 0.3, 0.1))
    
    def _generate_learning_suggestions(self):
        """Generate learning-based suggestions for improvement."""
        if not self.current_analysis:
            return
        
        suggestions = []
        
        # Robot recommendation suggestions
        robots = self.current_analysis['recommended_robots']
        if len(robots) > 1:
            suggestions.append({
                'type': 'robot_alternative',
                'message': f"Consider {robots[1]['robot']} for higher precision",
                'action': 'switch_robot',
                'data': robots[1]
            })
        
        # Process optimization suggestions
        optimizations = self.current_analysis.get('optimization_opportunities', [])
        for opt in optimizations[:2]:  # Top 2 optimizations
            suggestions.append({
                'type': 'optimization',
                'message': f"Optimize {opt['type']} for {opt['potential_improvement']*100:.0f}% improvement",
                'action': 'apply_optimization',
                'data': opt
            })
        
        # Safety suggestions
        safety_items = self.current_analysis.get('safety_considerations', [])
        critical_safety = [s for s in safety_items if s.get('priority') == 'critical']
        if critical_safety:
            suggestions.append({
                'type': 'safety_critical',
                'message': f"Critical safety requirement: {critical_safety[0]['requirement']}",
                'action': 'address_safety',
                'data': critical_safety[0]
            })
        
        self.ui_state['learning_suggestions'] = suggestions
    
    def _setup_viewport_overlay(self):
        """Setup viewport overlay for dashboard information."""
        
        # Register draw handler
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_dashboard_overlay,
            (),
            'WINDOW',
            'POST_PIXEL'
        )
    
    def _cleanup_viewport_overlay(self):
        """Cleanup viewport overlay."""
        
        if hasattr(self, '_draw_handler'):
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
    
    def _draw_dashboard_overlay(self):
        """Draw dashboard overlay information."""
        if not self.is_active or not self.current_analysis:
            return
        
        # Draw confidence meter
        self._draw_confidence_meter()
        
        # Draw robot recommendations
        self._draw_robot_recommendations()
        
        # Draw learning suggestions
        self._draw_learning_suggestions()
        
        # Draw engineering insights
        self._draw_engineering_insights()
    
    def _draw_confidence_meter(self):
        """Draw confidence meter overlay."""
        confidence = self.current_analysis.get('confidence_score', 0.0)
        
        # Position and size
        x, y = 50, bpy.context.region.height - 100
        width, height = 200, 20
        
        # Background
        vertices = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
        indices = [(0, 1, 2), (2, 3, 0)]
        
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        
        # Draw background
        shader.bind()
        shader.uniform_float("color", (0.2, 0.2, 0.2, 0.5))
        batch.draw(shader)
        
        # Draw confidence bar
        conf_width = width * confidence
        conf_vertices = [(x, y), (x + conf_width, y), (x + conf_width, y + height), (x, y + height)]
        conf_batch = batch_for_shader(shader, 'TRIS', {"pos": conf_vertices}, indices=indices)
        
        # Color based on confidence
        if confidence > 0.8:
            color = (0, 1, 0, 0.8)  # Green
        elif confidence > 0.5:
            color = (1, 1, 0, 0.8)  # Yellow
        else:
            color = (1, 0, 0, 0.8)  # Red
        
        shader.uniform_float("color", color)
        conf_batch.draw(shader)
        
        # Draw text
        font_id = 0
        blf.position(font_id, x, y + height + 5, 0)
        blf.size(font_id, 12, 72)
        blf.color(font_id, 1, 1, 1, 1)
        blf.draw(font_id, f"Engineering Confidence: {confidence:.1%}")
    
    def _draw_robot_recommendations(self):
        """Draw robot recommendations overlay."""
        robots = self.current_analysis.get('recommended_robots', [])
        if not robots:
            return
        
        # Position
        x, y = 50, bpy.context.region.height - 200
        
        font_id = 0
        blf.size(font_id, 14, 72)
        blf.color(font_id, 0.8, 0.9, 1, 1)
        
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, "🤖 Recommended Robots:")
        
        # Draw top 3 recommendations
        for i, robot in enumerate(robots[:3]):
            y_pos = y - 25 - (i * 20)
            score = robot['suitability_score']
            
            blf.position(font_id, x + 20, y_pos, 0)
            blf.size(font_id, 12, 72)
            blf.color(font_id, 1, 1, 1, 1)
            blf.draw(font_id, f"{i+1}. {robot['robot']} ({score:.1%})")
    
    def _draw_learning_suggestions(self):
        """Draw learning suggestions overlay."""
        suggestions = self.ui_state.get('learning_suggestions', [])
        if not suggestions:
            return
        
        # Position
        x, y = bpy.context.region.width - 350, bpy.context.region.height - 100
        
        font_id = 0
        blf.size(font_id, 14, 72)
        blf.color(font_id, 1, 0.9, 0.5, 1)
        
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, "💡 Smart Suggestions:")
        
        # Draw suggestions
        for i, suggestion in enumerate(suggestions[:3]):
            y_pos = y - 25 - (i * 20)
            
            blf.position(font_id, x + 20, y_pos, 0)
            blf.size(font_id, 11, 72)
            blf.color(font_id, 1, 1, 1, 1)
            blf.draw(font_id, suggestion['message'])
    
    def _draw_engineering_insights(self):
        """Draw engineering insights overlay."""
        process_type = self.current_analysis.get('process_type')
        if not process_type:
            return
        
        # Position
        x, y = 50, 50
        
        font_id = 0
        blf.size(font_id, 12, 72)
        blf.color(font_id, 0.7, 0.9, 0.7, 1)
        
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, f"🔧 Process: {process_type.replace('_', ' ').title()}")
        
        # Draw optimization opportunities
        optimizations = self.current_analysis.get('optimization_opportunities', [])
        if optimizations:
            y_pos = y - 20
            blf.position(font_id, x, y_pos, 0)
            blf.draw(font_id, f"⚡ {len(optimizations)} optimization opportunities detected")


# Blender UI Integration
class SMART_DASHBOARD_PT_main(Panel):
    """Main smart dashboard panel."""
    bl_label = "Smart Dashboard"
    bl_idname = "SMART_DASHBOARD_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ProcessAnimator"
    
    def draw(self, context):
        layout = self.layout
        
        # Dashboard activation
        row = layout.row()
        if hasattr(context.scene, 'smart_dashboard') and context.scene.smart_dashboard.is_active:
            row.operator("smart_dashboard.deactivate", text="Deactivate Dashboard", icon='PAUSE')
        else:
            row.operator("smart_dashboard.activate", text="Activate Dashboard", icon='PLAY')
        
        # Real-time description input
        layout.separator()
        layout.label(text="Describe Your Process:", icon='EDIT')
        
        if hasattr(context.scene, 'process_animator_props'):
            props = context.scene.process_animator_props
            layout.prop(props, "process_description", text="")
            
            # Show real-time analysis results
            if hasattr(context.scene, 'smart_dashboard'):
                dashboard = context.scene.smart_dashboard
                if dashboard.current_analysis:
                    self._draw_analysis_summary(layout, dashboard.current_analysis)
    
    def _draw_analysis_summary(self, layout, analysis):
        """Draw analysis summary in the panel."""
        
        if not analysis['success']:
            layout.label(text="❌ Analysis failed", icon='ERROR')
            return
        
        # Confidence indicator
        confidence = analysis['confidence_score']
        conf_text = f"Confidence: {confidence:.1%}"
        
        if confidence > 0.8:
            layout.label(text=f"✅ {conf_text}", icon='CHECKMARK')
        elif confidence > 0.5:
            layout.label(text=f"⚠️ {conf_text}", icon='ERROR')
        else:
            layout.label(text=f"❌ {conf_text}", icon='CANCEL')
        
        # Process type
        if analysis['process_type']:
            layout.label(text=f"Process: {analysis['process_type'].replace('_', ' ').title()}")
        
        # Top robot recommendation
        if analysis['recommended_robots']:
            top_robot = analysis['recommended_robots'][0]
            layout.label(text=f"Robot: {top_robot['robot']}")
            layout.label(text=f"Score: {top_robot['suitability_score']:.1%}")


class SMART_DASHBOARD_OT_activate(Operator):
    """Activate smart dashboard."""
    bl_idname = "smart_dashboard.activate"
    bl_label = "Activate Smart Dashboard"
    bl_description = "Activate real-time smart dashboard"
    
    def execute(self, context):
        if not hasattr(context.scene, 'smart_dashboard'):
            context.scene.smart_dashboard = SmartDashboard()
        
        context.scene.smart_dashboard.activate_dashboard()
        self.report({'INFO'}, "Smart Dashboard activated")
        return {'FINISHED'}


class SMART_DASHBOARD_OT_deactivate(Operator):
    """Deactivate smart dashboard."""
    bl_idname = "smart_dashboard.deactivate"
    bl_label = "Deactivate Smart Dashboard"
    bl_description = "Deactivate real-time smart dashboard"
    
    def execute(self, context):
        if hasattr(context.scene, 'smart_dashboard'):
            context.scene.smart_dashboard.deactivate_dashboard()
        
        self.report({'INFO'}, "Smart Dashboard deactivated")
        return {'FINISHED'}


# Import required for math operations
import math


# Registration
classes = [
    SMART_DASHBOARD_PT_main,
    SMART_DASHBOARD_OT_activate,
    SMART_DASHBOARD_OT_deactivate,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 