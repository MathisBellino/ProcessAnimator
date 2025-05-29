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
    
    MODULES_LOADED = True
    print("✅ All linkage animator modules loaded successfully")
    
except ImportError as e:
    MODULES_LOADED = False
    print(f"⚠️  Module import failed: {e}")
    print("Running in basic mode")

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
    ]

    def register():
        """Register addon classes and properties."""
        
        # Register classes
        for cls in classes:
            bpy.utils.register_class(cls)
        
        # Register properties
        bpy.types.Scene.linkage_properties = PointerProperty(type=LinkageProperties)
        
        print("✅ Multi-Bar Linkage Animator registered successfully")

    def unregister():
        """Unregister addon classes and properties."""
        
        # Unregister properties
        del bpy.types.Scene.linkage_properties
        
        # Unregister classes
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        
        print("Multi-Bar Linkage Animator unregistered")

else:
    # Blender not available - define dummy functions
    def register():
        print("Blender not available - cannot register addon")

    def unregister():
        print("Blender not available - nothing to unregister")

if __name__ == "__main__":
    if BLENDER_AVAILABLE:
        register()
    else:
        print("Multi-Bar Linkage Animator - Standalone mode") 