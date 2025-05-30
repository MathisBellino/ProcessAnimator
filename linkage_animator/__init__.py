#!/usr/bin/env python3
"""
Multi-Bar Linkage Animator - Blender Addon

Automatically creates and animates multi-bar linkage mechanisms with:
- Automatic armature and bone setup
- Constraint-based animation
- Physics simulation
- Multiple linkage types (four-bar, slider-crank, six-bar, etc.)
"""

bl_info = {
    "name": "Multi-Bar Linkage Animator",
    "author": "Robot Animator Plus Delux 3000",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Linkage Animator",
    "description": "Automatically create and animate multi-bar linkage mechanisms",
    "category": "Animation",
    "doc_url": "https://github.com/your-repo/linkage-animator",
    "tracker_url": "https://github.com/your-repo/linkage-animator/issues",
}

import logging
import sys
import os

# Check if Blender is available
try:
    import bpy
    import bmesh
    import mathutils
    from mathutils import Vector, Matrix, Euler
    from bpy.types import Panel, Operator, PropertyGroup, AddonPreferences
    from bpy.props import (
        StringProperty, FloatProperty, IntProperty, BoolProperty, 
        EnumProperty, FloatVectorProperty, PointerProperty
    )
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: Blender modules not available. Running in standalone mode.")

# Add current addon path to Python path
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import addon modules
try:
    from .core.linkage_mechanisms import FourBarLinkage, SliderCrankMechanism, SixBarLinkage
    from .core.constraint_solver import ConstraintSolver
    from .blender.auto_setup import BlenderAutoSetup
    from .animation.linkage_animator import LinkageAnimator
    from .animation.keyframe_generator import KeyframeGenerator
    
    # Import simplified UI
    if BLENDER_AVAILABLE:
        from .ui.simplified_ui import register_studio_ui, unregister_studio_ui
    
    MODULES_LOADED = True
    print("✅ All linkage animator modules loaded successfully")
    
except ImportError as e:
    MODULES_LOADED = False
    print(f"⚠️  Module import failed: {e}")
    print("Running in basic mode")

# Import new systems
try:
    from .ui.startup_wizard import register_startup_wizard, unregister_startup_wizard
    from .ai.parameter_assistant import register_ai_assistant, unregister_ai_assistant
    from .core.scene_builder import register_scene_builder, unregister_scene_builder
    NEW_SYSTEMS_AVAILABLE = True
except ImportError as e:
    NEW_SYSTEMS_AVAILABLE = False
    print(f"⚠️  New systems import failed: {e}")

# Import new feature modules
from .features import bone_visibility
from .features import natural_language_execution
from .features import solidworks_cad_tools
from .features import groot_integration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Only define Blender-specific classes if Blender is available
if BLENDER_AVAILABLE:
    # Property Groups for Linkage Configuration
    class LinkageProperties(PropertyGroup):
        """Properties for linkage configuration."""
        
        linkage_type: EnumProperty(
            name="Linkage Type",
            description="Type of linkage mechanism to create",
            items=[
                ('four_bar', "Four-Bar Linkage", "Classic four-bar linkage mechanism"),
                ('slider_crank', "Slider-Crank", "Slider-crank mechanism"),
                ('six_bar', "Six-Bar Linkage", "Six-bar linkage mechanism"),
                ('scotch_yoke', "Scotch Yoke", "Scotch yoke mechanism"),
                ('geneva', "Geneva Drive", "Geneva wheel mechanism"),
                ('cam_follower', "Cam-Follower", "Cam and follower mechanism"),
            ],
            default='four_bar'
        )
        
        # Four-bar linkage properties
        ground_length: FloatProperty(
            name="Ground Link Length",
            description="Length of the ground link",
            default=10.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        input_length: FloatProperty(
            name="Input Link Length",
            description="Length of the input (driver) link",
            default=3.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        coupler_length: FloatProperty(
            name="Coupler Link Length",
            description="Length of the coupler link",
            default=8.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        output_length: FloatProperty(
            name="Output Link Length",
            description="Length of the output (follower) link",
            default=5.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        # Slider-crank properties
        crank_length: FloatProperty(
            name="Crank Length",
            description="Length of the crank",
            default=2.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        connecting_rod_length: FloatProperty(
            name="Connecting Rod Length",
            description="Length of the connecting rod",
            default=6.0,
            min=0.1,
            max=100.0,
            unit='LENGTH'
        )
        
        # Animation properties
        animation_duration: FloatProperty(
            name="Animation Duration",
            description="Duration of one complete cycle (seconds)",
            default=2.0,
            min=0.1,
            max=60.0
        )
        
        input_rpm: FloatProperty(
            name="Input RPM",
            description="Rotational speed of input link (RPM)",
            default=60.0,
            min=1.0,
            max=1000.0
        )
        
        show_constraints: BoolProperty(
            name="Show Constraints",
            description="Visualize constraint relationships",
            default=True
        )
        
        show_motion_path: BoolProperty(
            name="Show Motion Path",
            description="Show the motion path of key points",
            default=True
        )
        
        auto_keyframe: BoolProperty(
            name="Auto Keyframe",
            description="Automatically generate keyframes for animation",
            default=True
        )
        
        linkage_name: StringProperty(
            name="Linkage Name",
            description="Name for the linkage mechanism",
            default="Linkage_Mechanism"
        )

    # Main Operators
    class LINKAGE_OT_create_mechanism(Operator):
        """Create a new linkage mechanism with automatic setup."""
        bl_idname = "linkage.create_mechanism"
        bl_label = "Create Linkage Mechanism"
        bl_description = "Automatically create linkage mechanism with bones and constraints"
        bl_options = {'REGISTER', 'UNDO'}
        
        def execute(self, context):
            if not MODULES_LOADED:
                self.report({'ERROR'}, "Linkage animator modules not loaded properly")
                return {'CANCELLED'}
            
            try:
                props = context.scene.linkage_properties
                
                # Create auto setup instance
                auto_setup = BlenderAutoSetup()
                
                # Prepare linkage configuration
                if props.linkage_type == 'four_bar':
                    linkage_config = {
                        'type': 'four_bar',
                        'ground_length': props.ground_length,
                        'input_length': props.input_length,
                        'coupler_length': props.coupler_length,
                        'output_length': props.output_length,
                        'name': props.linkage_name
                    }
                elif props.linkage_type == 'slider_crank':
                    linkage_config = {
                        'type': 'slider_crank',
                        'crank_length': props.crank_length,
                        'connecting_rod_length': props.connecting_rod_length,
                        'name': props.linkage_name
                    }
                else:
                    self.report({'ERROR'}, f"Linkage type '{props.linkage_type}' not yet implemented")
                    return {'CANCELLED'}
                
                # Create the linkage
                result = auto_setup.create_linkage_armature(linkage_config)
                
                if result['success']:
                    armature_obj = result['armature_object']
                    
                    # Select the created armature
                    bpy.context.view_layer.objects.active = armature_obj
                    armature_obj.select_set(True)
                    
                    # Switch to pose mode for animation
                    bpy.context.view_layer.objects.active = armature_obj
                    bpy.ops.object.mode_set(mode='POSE')
                    
                    self.report({'INFO'}, f"Created {props.linkage_type} linkage: {props.linkage_name}")
                    
                    # Store linkage info for animation
                    armature_obj['linkage_config'] = linkage_config
                    
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, f"Failed to create linkage: {result.get('error', 'Unknown error')}")
                    return {'CANCELLED'}
                    
            except Exception as e:
                self.report({'ERROR'}, f"Error creating linkage: {str(e)}")
                logger.error(f"Linkage creation error: {e}")
                return {'CANCELLED'}

    class LINKAGE_OT_animate_mechanism(Operator):
        """Generate animation for the linkage mechanism."""
        bl_idname = "linkage.animate_mechanism"
        bl_label = "Animate Linkage"
        bl_description = "Generate keyframe animation for the linkage mechanism"
        bl_options = {'REGISTER', 'UNDO'}
        
        def execute(self, context):
            if not MODULES_LOADED:
                self.report({'ERROR'}, "Linkage animator modules not loaded properly")
                return {'CANCELLED'}
            
            try:
                props = context.scene.linkage_properties
                active_obj = context.active_object
                
                if not active_obj or active_obj.type != 'ARMATURE':
                    self.report({'ERROR'}, "Please select a linkage armature")
                    return {'CANCELLED'}
                
                # Get linkage configuration from object
                linkage_config = active_obj.get('linkage_config')
                if not linkage_config:
                    self.report({'ERROR'}, "Selected armature is not a linkage mechanism")
                    return {'CANCELLED'}
                
                # Create animator
                animator = LinkageAnimator()
                
                # Prepare animation request
                animation_request = {
                    'linkage_type': linkage_config['type'],
                    'parameters': linkage_config,
                    'motion': {
                        'type': 'constant_rotation',
                        'rpm': props.input_rpm,
                        'duration': props.animation_duration
                    },
                    'visualization': {
                        'show_constraints': props.show_constraints,
                        'show_motion_path': props.show_motion_path,
                        'quality': 'medium'
                    },
                    'armature_object': active_obj
                }
                
                # Generate animation
                result = animator.create_animation(animation_request)
                
                if result['success']:
                    frame_count = result['frame_count']
                    
                    # Set scene frame range
                    context.scene.frame_start = 1
                    context.scene.frame_end = frame_count
                    context.scene.frame_current = 1
                    
                    self.report({'INFO'}, f"Animation created: {frame_count} frames")
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, f"Animation failed: {result.get('error', 'Unknown error')}")
                    return {'CANCELLED'}
                    
            except Exception as e:
                self.report({'ERROR'}, f"Animation error: {str(e)}")
                logger.error(f"Animation error: {e}")
                return {'CANCELLED'}

    class LINKAGE_OT_analyze_mechanism(Operator):
        """Analyze linkage mechanism properties."""
        bl_idname = "linkage.analyze_mechanism"
        bl_label = "Analyze Linkage"
        bl_description = "Analyze linkage mechanism properties and motion"
        
        def execute(self, context):
            try:
                props = context.scene.linkage_properties
                
                if props.linkage_type == 'four_bar':
                    linkage = FourBarLinkage(
                        props.ground_length,
                        props.input_length,
                        props.coupler_length,
                        props.output_length
                    )
                    
                    grashof = linkage.check_grashof_condition()
                    
                    message = f"Four-bar Analysis:\n"
                    message += f"Type: {grashof['type']}\n"
                    message += f"Grashof: {'Yes' if grashof['is_grashof'] else 'No'}\n"
                    message += f"Motion: {grashof.get('motion_type', 'Unknown')}"
                    
                    self.report({'INFO'}, message)
                    
                    # Show in UI
                    def draw_analysis(self, context):
                        layout = self.layout
                        layout.label(text="Linkage Analysis Results:")
                        layout.label(text=f"Type: {grashof['type']}")
                        layout.label(text=f"Grashof Condition: {'Satisfied' if grashof['is_grashof'] else 'Not Satisfied'}")
                        layout.label(text=f"Expected Motion: {grashof.get('motion_type', 'Complex')}")
                    
                    context.window_manager.popup_menu(draw_analysis, title="Linkage Analysis", icon='INFO')
                    
                else:
                    self.report({'INFO'}, f"Analysis for {props.linkage_type} not yet implemented")
                
                return {'FINISHED'}
                
            except Exception as e:
                self.report({'ERROR'}, f"Analysis error: {str(e)}")
                return {'CANCELLED'}

    # Panels
    class LINKAGE_PT_main(Panel):
        """Main panel for linkage animator."""
        bl_label = "Linkage Animator"
        bl_idname = "LINKAGE_PT_main"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Linkage Animator"
        
        def draw(self, context):
            layout = self.layout
            props = context.scene.linkage_properties
            
            # Header
            box = layout.box()
            box.label(text="Multi-Bar Linkage Animator", icon='ARMATURE_DATA')
            box.label(text="Automatic Setup & Animation")
            
            # Linkage type selection
            layout.prop(props, "linkage_type")
            
            # Quick create button
            layout.separator()
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.operator("linkage.create_mechanism", icon='ADD')
            
            # Analysis button
            if props.linkage_type in ['four_bar']:
                layout.operator("linkage.analyze_mechanism", icon='VIEWZOOM')

    class LINKAGE_PT_parameters(Panel):
        """Panel for linkage parameters."""
        bl_label = "Linkage Parameters"
        bl_idname = "LINKAGE_PT_parameters"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Linkage Animator"
        bl_parent_id = "LINKAGE_PT_main"
        
        def draw(self, context):
            layout = self.layout
            props = context.scene.linkage_properties
            
            # Linkage name
            layout.prop(props, "linkage_name")
            
            # Parameters based on linkage type
            if props.linkage_type == 'four_bar':
                layout.label(text="Four-Bar Linkage:")
                layout.prop(props, "ground_length")
                layout.prop(props, "input_length")
                layout.prop(props, "coupler_length")
                layout.prop(props, "output_length")
                
            elif props.linkage_type == 'slider_crank':
                layout.label(text="Slider-Crank:")
                layout.prop(props, "crank_length")
                layout.prop(props, "connecting_rod_length")
                
            else:
                layout.label(text="Parameters coming soon...")

    class LINKAGE_PT_animation(Panel):
        """Panel for animation controls."""
        bl_label = "Animation"
        bl_idname = "LINKAGE_PT_animation"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Linkage Animator"
        bl_parent_id = "LINKAGE_PT_main"
        
        def draw(self, context):
            layout = self.layout
            props = context.scene.linkage_properties
            
            # Animation parameters
            layout.prop(props, "animation_duration")
            layout.prop(props, "input_rpm")
            
            layout.separator()
            
            # Visualization options
            layout.label(text="Visualization:")
            layout.prop(props, "show_constraints")
            layout.prop(props, "show_motion_path")
            layout.prop(props, "auto_keyframe")
            
            layout.separator()
            
            # Animation controls
            row = layout.row(align=True)
            row.scale_y = 1.2
            row.operator("linkage.animate_mechanism", icon='PLAY')

    # Registration
    classes = [
        LinkageProperties,
        LINKAGE_OT_create_mechanism,
        LINKAGE_OT_animate_mechanism,
        LINKAGE_OT_analyze_mechanism,
        LINKAGE_PT_main,
        LINKAGE_PT_parameters,
        LINKAGE_PT_animation,
        # New complete workflow classes
        ROBOTANIM_PT_complete_workflow,
        ROBOTANIM_PT_robot_catalogue,
        ROBOTANIM_PT_ai_assistant_panel,
        ROBOTANIM_PT_teaching_system,
        ROBOTANIM_OT_import_robot,
        ROBOTANIM_OT_use_suggestion,
    ]

    def register():
        """Register all addon classes and features."""
        try:
            # Core registration
            register_linkage_mechanisms()
            register_constraint_solver()
            register_auto_setup()
            register_animation_pipeline()
            
            # UI registration
            register_startup_wizard()
            register_simplified_ui()
            register_workspace_manager()
            
            # Robot system registration
            register_robot_catalogue()
            register_parameter_assistant()
            register_scene_builder()
            
            # New features registration
            bone_visibility.register_bone_visibility()
            natural_language_execution.register_natural_language()
            solidworks_cad_tools.register_solidworks_cad()
            groot_integration.register_groot_integration()
            
            # Register property groups and panels
            for cls in classes:
                bpy.utils.register_class(cls)
            
            # Initialize scene properties
            bpy.types.Scene.robot_animator_props = PointerProperty(type=RobotAnimatorProperties)
            
            logger.info("Robot Animator Plus Delux 3000 registered successfully")
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise


    def unregister():
        """Unregister all addon classes and features."""
        try:
            # Unregister new features
            groot_integration.unregister_groot_integration()
            solidworks_cad_tools.unregister_solidworks_cad()
            natural_language_execution.unregister_natural_language()
            bone_visibility.unregister_bone_visibility()
            
            # Unregister robot systems
            unregister_scene_builder()
            unregister_parameter_assistant()
            unregister_robot_catalogue()
            
            # Unregister UI systems
            unregister_workspace_manager()
            unregister_simplified_ui()
            unregister_startup_wizard()
            
            # Unregister core systems
            unregister_animation_pipeline()
            unregister_auto_setup()
            unregister_constraint_solver()
            unregister_linkage_mechanisms()
            
            # Unregister property groups and panels
            for cls in reversed(classes):
                bpy.utils.unregister_class(cls)
            
            # Remove scene properties
            if hasattr(bpy.types.Scene, 'robot_animator_props'):
                del bpy.types.Scene.robot_animator_props
            
            logger.info("Robot Animator Plus Delux 3000 unregistered successfully")
            
        except Exception as e:
            logger.error(f"Unregistration failed: {e}")

else:
    # Blender not available - define dummy functions
    def register():
        print("Blender not available - cannot register addon")

    def unregister():
        print("Blender not available - nothing to unregister")

# New comprehensive panels for complete workflow
class ROBOTANIM_PT_complete_workflow(Panel):
    """Complete Robot Animation Studio workflow panel"""
    bl_label = "🚀 Robot Animation Studio"
    bl_idname = "ROBOTANIM_PT_complete_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Check if startup wizard is needed
        if not hasattr(scene, 'robotanim_mode') or not scene.robotanim_mode:
            self.draw_startup_interface(layout, context)
        else:
            # Show mode-specific interface
            if scene.robotanim_mode == 'simple':
                self.draw_simple_workflow(layout, context)
            else:
                self.draw_professional_workflow(layout, context)
    
    def draw_startup_interface(self, layout, context):
        """Draw startup interface for first-time users."""
        # Welcome header
        header = layout.box()
        header.scale_y = 1.3
        header.label(text="🤖 Welcome to Robot Animation Studio!", icon='ARMATURE_DATA')
        
        # Quick description
        desc_box = layout.box()
        desc_box.label(text="Complete robot simulation & animation platform")
        desc_box.label(text="From simple drag-and-drop to professional workflows")
        
        # Large startup button
        setup_box = layout.box()
        setup_box.scale_y = 2.0
        setup_box.operator("robotanim.startup_wizard", 
                          text="🚀 Start Setup Wizard", 
                          icon='PLAY')
        
        # Quick mode selection for experienced users
        layout.separator()
        quick_box = layout.box()
        quick_box.label(text="Quick Start (skip wizard):", icon='FORWARD')
        
        row = quick_box.row(align=True)
        row.operator("robotanim.enter_simple_mode", text="Simple Mode", icon='RESTRICT_SELECT_OFF')
        row.operator("robotanim.enter_professional_mode", text="Pro Mode", icon='TOOL_SETTINGS')
    
    def draw_simple_workflow(self, layout, context):
        """Draw simplified workflow for beginners."""
        # Mode indicator
        mode_box = layout.box()
        mode_row = mode_box.row()
        mode_row.label(text="🎨 Simple Mode", icon='RESTRICT_SELECT_OFF')
        mode_row.operator("robotanim.enter_professional_mode", text="", icon='TOOL_SETTINGS')
        
        # Step-by-step workflow
        self.draw_workflow_steps(layout, context, mode='simple')
    
    def draw_professional_workflow(self, layout, context):
        """Draw professional workflow interface."""
        # Mode indicator
        mode_box = layout.box()
        mode_row = mode_box.row()
        mode_row.label(text="🔧 Professional Mode", icon='TOOL_SETTINGS')
        mode_row.operator("robotanim.enter_simple_mode", text="", icon='RESTRICT_SELECT_OFF')
        
        # Step-by-step workflow
        self.draw_workflow_steps(layout, context, mode='professional')
    
    def draw_workflow_steps(self, layout, context, mode='simple'):
        """Draw workflow steps based on mode."""
        
        # Step 1: Robot Selection
        step1_box = layout.box()
        step1_box.label(text="1️⃣ Choose Your Robot", icon='ARMATURE_DATA')
        
        if mode == 'simple':
            step1_box.operator("robotanim.browse_robots", 
                              text="🤖 Browse Robot Catalogue", 
                              icon='WORLD_DATA')
        else:
            row = step1_box.row(align=True)
            row.operator("robotanim.browse_robots", text="Browse Catalogue", icon='WORLD_DATA')
            row.operator("robotanim.connect_catalogue", text="", icon='URL')
        
        # Step 2: AI Assistant
        step2_box = layout.box()
        step2_box.label(text="2️⃣ Describe Your Task", icon='TOOL_SETTINGS')
        
        ai_props = getattr(context.scene, 'ai_assistant', None)
        if ai_props and ai_props.conversation_active:
            # Show active conversation
            conv_box = step2_box.box()
            conv_box.label(text="💬 AI Assistant:", icon='CHAT')
            
            # Current question
            if ai_props.current_question:
                question_lines = ai_props.current_question.split('\n')
                for line in question_lines:
                    conv_box.label(text=line)
            
            # Response input
            conv_box.prop(ai_props, "user_response", text="Your Answer")
            
            # Guided suggestions (simplified)
            if mode == 'simple':
                suggestions = ["pick up small parts", "weld metal joints", "assemble components"]
                sug_row = conv_box.row(align=True)
                for sug in suggestions[:2]:
                    op = sug_row.operator("robotanim.use_suggestion", text=sug)
                    op.suggestion = sug
            
            # Submit button
            submit_row = conv_box.row(align=True)
            submit_row.scale_y = 1.5
            submit_row.operator("robotanim.respond_to_ai", 
                               text="Submit Answer", 
                               icon='CHECKMARK')
            
            # Confidence indicator
            confidence = ai_props.confidence_level
            if confidence > 0:
                conf_box = step2_box.box()
                conf_box.label(text=f"🎯 Understanding: {confidence*100:.0f}%")
                
                if confidence >= 0.8:
                    conf_box.operator("robotanim.finalize_ai_setup", 
                                     text="✅ Generate Scene", 
                                     icon='SCENE_DATA')
        else:
            # Start AI assistant
            step2_box.operator("robotanim.start_ai_assistant", 
                              text="🧠 Start AI Assistant", 
                              icon='CHAT')
        
        # Step 3: Scene Building
        step3_box = layout.box()
        step3_box.label(text="3️⃣ Build Animation Scene", icon='SCENE_DATA')
        
        scene_config = context.scene.get('ai_animation_config')
        if scene_config:
            step3_box.label(text="✅ Configuration Ready", icon='CHECKMARK')
            step3_box.operator("robotanim.build_ai_scene", 
                              text="🏗️ Build Scene", 
                              icon='SCENE_DATA')
        else:
            step3_box.label(text="Complete AI setup first", icon='INFO')
        
        # Step 4: Interactive Teaching
        step4_box = layout.box()
        step4_box.label(text="4️⃣ Teach Robot Positions", icon='ORIENTATION_CURSOR')
        
        scene_components = context.scene.get('scene_components')
        if scene_components:
            # Teaching controls
            teach_row = step4_box.row(align=True)
            
            drag_mode = context.scene.get('drag_mode', False)
            if drag_mode:
                teach_row.operator("robotanim.toggle_drag_mode", 
                                  text="Exit Drag Mode", 
                                  icon='RESTRICT_SELECT_ON')
            else:
                teach_row.operator("robotanim.toggle_drag_mode", 
                                  text="Enable Drag Mode", 
                                  icon='ORIENTATION_CURSOR')
            
            teach_row.operator("robotanim.capture_coordinate", 
                              text="Capture Position", 
                              icon='PLUS')
            
            # Show captured coordinates count
            captured = context.scene.get('captured_coordinates', [])
            if captured:
                step4_box.label(text=f"📍 Captured: {len(captured)} positions")
        else:
            step4_box.label(text="Build scene first", icon='INFO')
        
        # Step 5: Animation
        step5_box = layout.box()
        step5_box.label(text="5️⃣ Generate Animation", icon='PLAY')
        
        captured_coords = context.scene.get('captured_coordinates', [])
        if captured_coords and len(captured_coords) >= 2:
            step5_box.operator("linkage.animate_mechanism", 
                              text="🎬 Create Animation", 
                              icon='RENDER_ANIMATION')
        else:
            step5_box.label(text="Capture teaching points first", icon='INFO')


class ROBOTANIM_PT_robot_catalogue(Panel):
    """Robot catalogue browser panel"""
    bl_label = "🤖 Robot Catalogue"
    bl_idname = "ROBOTANIM_PT_robot_catalogue"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    def draw(self, context):
        layout = self.layout
        
        # Catalogue connection status
        startup_wizard = getattr(context.scene, 'startup_wizard', None)
        if startup_wizard and startup_wizard.robot_catalogue_connected:
            layout.label(text="✅ Catalogue Connected", icon='WORLD_DATA')
            
            # Featured robots
            featured_box = layout.box()
            featured_box.label(text="⭐ Featured Robots:")
            
            featured_robots = [
                ("ur5e", "Universal Robots UR5e", "Collaborative"),
                ("kuka_kr10", "KUKA KR10", "Industrial"),
                ("abb_irb120", "ABB IRB 120", "Compact")
            ]
            
            for robot_id, name, type_name in featured_robots:
                robot_row = featured_box.row()
                robot_row.label(text=f"{name} ({type_name})")
                import_op = robot_row.operator("robotanim.import_robot", text="Import")
                import_op.robot_id = robot_id
        else:
            layout.operator("robotanim.connect_catalogue", 
                           text="🔗 Connect to Catalogue", 
                           icon='URL')


class ROBOTANIM_PT_ai_assistant_panel(Panel):
    """AI Parameter Assistant panel"""
    bl_label = "🧠 AI Assistant"
    bl_idname = "ROBOTANIM_PT_ai_assistant_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    @classmethod
    def poll(cls, context):
        # Only show if in simple mode or professional mode with AI enabled
        return getattr(context.scene, 'robotanim_mode', '') in ['simple', 'professional']
    
    def draw(self, context):
        layout = self.layout
        
        ai_props = getattr(context.scene, 'ai_assistant', None)
        if not ai_props:
            layout.operator("robotanim.start_ai_assistant", 
                           text="Start AI Assistant", 
                           icon='CHAT')
            return
        
        if ai_props.conversation_active:
            # Conversation interface
            conv_box = layout.box()
            conv_box.label(text=f"Phase: {ai_props.setup_phase.title()}")
            
            # Progress indicator
            progress = ai_props.confidence_level
            prog_box = conv_box.box()
            prog_box.label(text=f"Progress: {progress*100:.0f}%")
            
            # Progress bar visualization
            prog_row = prog_box.row()
            prog_row.scale_y = 0.5
            for i in range(10):
                if i < (progress * 10):
                    prog_row.label(text="█")
                else:
                    prog_row.label(text="░")
        else:
            layout.label(text="AI Assistant Ready", icon='CHECKMARK')


class ROBOTANIM_PT_teaching_system(Panel):
    """Interactive teaching system panel"""
    bl_label = "🎯 Teaching System"
    bl_idname = "ROBOTANIM_PT_teaching_system"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    @classmethod
    def poll(cls, context):
        # Only show if scene has been built
        return context.scene.get('scene_components') is not None
    
    def draw(self, context):
        layout = self.layout
        
        # Teaching mode status
        drag_mode = context.scene.get('drag_mode', False)
        
        mode_box = layout.box()
        if drag_mode:
            mode_box.alert = True
            mode_box.label(text="🎯 Teaching Mode Active", icon='ORIENTATION_CURSOR')
            mode_box.label(text="Drag objects to teach positions")
        else:
            mode_box.label(text="Teaching Mode Inactive")
        
        # Controls
        control_row = layout.row(align=True)
        if drag_mode:
            control_row.operator("robotanim.toggle_drag_mode", 
                                text="Exit Teaching", 
                                icon='RESTRICT_SELECT_ON')
        else:
            control_row.operator("robotanim.toggle_drag_mode", 
                                text="Start Teaching", 
                                icon='ORIENTATION_CURSOR')
        
        control_row.operator("robotanim.capture_coordinate", 
                            text="Capture", 
                            icon='PLUS')
        
        # Teaching points summary
        captured = context.scene.get('captured_coordinates', [])
        teaching_collection = bpy.data.collections.get("Teaching_Points")
        
        summary_box = layout.box()
        summary_box.label(text="📊 Teaching Summary:")
        
        if teaching_collection:
            summary_box.label(text=f"Teaching Points: {len(teaching_collection.objects)}")
        
        if captured:
            summary_box.label(text=f"Captured Positions: {len(captured)}")
            
            # Show recent captures
            if len(captured) > 0:
                recent_box = summary_box.box()
                recent_box.label(text="Recent Captures:")
                for i, coord in enumerate(captured[-3:]):  # Show last 3
                    loc = coord['location']
                    recent_box.label(text=f"  {i+1}: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f})")


# Additional operators for complete workflow
class ROBOTANIM_OT_import_robot(Operator):
    """Import specific robot from catalogue"""
    bl_idname = "robotanim.import_robot"
    bl_label = "Import Robot"
    bl_options = {'REGISTER', 'UNDO'}
    
    robot_id: StringProperty(default="")
    
    def execute(self, context):
        if not NEW_SYSTEMS_AVAILABLE:
            self.report({'ERROR'}, "Robot catalogue system not available")
            return {'CANCELLED'}
        
        from .core.robot_catalogue import robot_catalogue
        
        result = robot_catalogue.import_robot_to_scene(self.robot_id)
        
        if result['success']:
            self.report({'INFO'}, result['message'])
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result.get('error', 'Import failed'))
            return {'CANCELLED'}


class ROBOTANIM_OT_use_suggestion(Operator):
    """Use AI suggestion for quick input"""
    bl_idname = "robotanim.use_suggestion"
    bl_label = "Use Suggestion"
    bl_options = {'REGISTER', 'UNDO'}
    
    suggestion: StringProperty(default="")
    
    def execute(self, context):
        ai_props = getattr(context.scene, 'ai_assistant', None)
        if ai_props:
            ai_props.user_response = self.suggestion
            # Automatically submit
            bpy.ops.robotanim.respond_to_ai()
        
        return {'FINISHED'}

if __name__ == "__main__":
    if BLENDER_AVAILABLE:
        register()
    else:
        print("Multi-Bar Linkage Animator - Standalone mode") 