#!/usr/bin/env python3
"""
Simplified UI for Robot Animation Studio

Beginner-friendly interface that hides Blender complexity and focuses
on robot/mechanism animation workflow.
"""

import bpy
from bpy.types import Panel, Operator, WorkSpaceKeyConfig
from bpy.props import BoolProperty
import bmesh
from .workspace_manager import WorkspaceManager, register_workspace_manager, unregister_workspace_manager


class ROBOTANIM_OT_enter_studio_mode(Operator):
    """Enter Robot Animation Studio Mode - Simplified interface for beginners"""
    bl_idname = "robotanim.enter_studio_mode"
    bl_label = "Enter Robot Animation Studio"
    bl_description = "Switch to beginner-friendly robot animation interface"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Store current UI state
        context.scene.robotanim_studio_mode = True
        
        # Configure viewport for robot animation
        self.setup_viewport_for_animation(context)
        
        # Hide complex Blender panels
        self.hide_complex_ui(context)
        
        # Switch to studio workspace
        manager = WorkspaceManager()
        studio_workspace = manager.create_robot_studio_workspace()
        context.window.workspace = studio_workspace
        manager.enter_beginner_mode(context)
        
        # Show welcome message
        self.report({'INFO'}, "Welcome to Robot Animation Studio! Build and animate mechanisms easily.")
        
        return {'FINISHED'}
    
    def setup_viewport_for_animation(self, context):
        """Configure viewport for optimal robot animation view."""
        # Set to solid shading mode
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        space.show_gizmo = True
                        space.show_gizmo_object_translate = True
                        space.show_gizmo_object_rotate = True
                        space.show_gizmo_object_scale = False  # Hide scale gizmo
                        space.overlay.show_grid = True
                        space.overlay.show_axis_x = True
                        space.overlay.show_axis_y = True
                        space.overlay.show_axis_z = True
                        
                        # Set good camera angle for mechanisms
                        space.region_3d.view_perspective = 'PERSP'
    
    def hide_complex_ui(self, context):
        """Hide complex Blender UI elements for beginners."""
        # This will be handled by custom panels that only show when needed
        pass


class ROBOTANIM_OT_exit_studio_mode(Operator):
    """Exit Robot Animation Studio Mode - Return to full Blender interface"""
    bl_idname = "robotanim.exit_studio_mode"
    bl_label = "Exit Studio Mode"
    bl_description = "Return to full Blender interface"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.robotanim_studio_mode = False
        self.report({'INFO'}, "Returned to full Blender interface")
        return {'FINISHED'}


class ROBOTANIM_PT_studio_main(Panel):
    """Main Robot Animation Studio panel with simplified workflow"""
    bl_label = "🤖 Robot Animation Studio"
    bl_idname = "ROBOTANIM_PT_studio_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Check if in studio mode
        studio_mode = getattr(scene, 'robotanim_studio_mode', False)
        
        if not studio_mode:
            # Entry point to studio mode
            box = layout.box()
            box.label(text="Welcome!", icon='ARMATURE_DATA')
            box.label(text="Ready to animate robots?")
            
            col = box.column(align=True)
            col.scale_y = 2.0
            col.operator("robotanim.enter_studio_mode", 
                        text="Start Robot Animation Studio", 
                        icon='PLAY')
            
            box.separator()
            box.label(text="For advanced users:")
            box.operator("robotanim.exit_studio_mode", 
                        text="Use Full Blender Interface", 
                        icon='PREFERENCES')
        else:
            # Studio mode interface
            self.draw_studio_interface(layout, context)
    
    def draw_studio_interface(self, layout, context):
        """Draw the simplified studio interface."""
        # Header with mode indicator
        header = layout.box()
        row = header.row()
        row.label(text="🎬 Animation Studio Mode", icon='ARMATURE_DATA')
        row.operator("robotanim.exit_studio_mode", text="", icon='X')
        
        layout.separator()
        
        # Quick start section
        quick_box = layout.box()
        quick_box.label(text="🚀 Quick Start", icon='ZOOMIN')
        
        col = quick_box.column(align=True)
        col.scale_y = 1.5
        
        # Large, clear buttons for main actions
        col.operator("linkage.create_mechanism", 
                    text="🔧 Create New Mechanism", 
                    icon='ADD')
        
        # Only show animation button if armature is selected
        if (context.active_object and 
            context.active_object.type == 'ARMATURE' and 
            'linkage_config' in context.active_object):
            col.operator("linkage.animate_mechanism", 
                        text="🎬 Animate Mechanism", 
                        icon='PLAY')
        
        layout.separator()
        
        # Mechanism gallery
        gallery_box = layout.box()
        gallery_box.label(text="📚 Mechanism Gallery", icon='PRESET')
        
        # Quick preset buttons
        preset_col = gallery_box.column(align=True)
        preset_col.operator("robotanim.create_preset", 
                           text="⚙️ Four-Bar Linkage").preset_type = 'four_bar_basic'
        preset_col.operator("robotanim.create_preset", 
                           text="🔄 Slider-Crank Engine").preset_type = 'slider_crank_engine'
        preset_col.operator("robotanim.create_preset", 
                           text="🦾 Robot Arm Joint").preset_type = 'robot_arm_joint'


class ROBOTANIM_PT_studio_build(Panel):
    """Simplified mechanism building panel"""
    bl_label = "🔧 Build Mechanism"
    bl_idname = "ROBOTANIM_PT_studio_build"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_studio_main"
    
    @classmethod
    def poll(cls, context):
        return getattr(context.scene, 'robotanim_studio_mode', False)
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.linkage_properties
        
        # Mechanism type with big icons
        layout.label(text="Choose Your Mechanism:")
        
        # Visual mechanism selector
        grid = layout.grid_flow(columns=2, align=True)
        
        # Four-bar linkage
        fourbar_box = grid.box()
        fourbar_box.scale_y = 1.2
        if props.linkage_type == 'four_bar':
            fourbar_box.alert = True
        fourbar_col = fourbar_box.column(align=True)
        fourbar_col.operator("robotanim.select_mechanism", 
                            text="Four-Bar Linkage", 
                            icon='MESH_GRID').mech_type = 'four_bar'
        fourbar_col.label(text="Classic mechanism")
        
        # Slider-crank
        slider_box = grid.box()
        slider_box.scale_y = 1.2
        if props.linkage_type == 'slider_crank':
            slider_box.alert = True
        slider_col = slider_box.column(align=True)
        slider_col.operator("robotanim.select_mechanism", 
                           text="Slider-Crank", 
                           icon='FORWARD').mech_type = 'slider_crank'
        slider_col.label(text="Engine piston")
        
        layout.separator()
        
        # Simple parameter controls
        if props.linkage_type == 'four_bar':
            self.draw_fourbar_simple_params(layout, props)
        elif props.linkage_type == 'slider_crank':
            self.draw_slider_simple_params(layout, props)
        
        layout.separator()
        
        # Analysis for beginners
        analysis_box = layout.box()
        analysis_box.label(text="🔍 Check Your Design", icon='VIEWZOOM')
        analysis_box.operator("linkage.analyze_mechanism", 
                             text="Analyze Motion", 
                             icon='PHYSICS')
    
    def draw_fourbar_simple_params(self, layout, props):
        """Simplified four-bar parameters with visual aids."""
        layout.label(text="📏 Adjust Sizes:", icon='RULER')
        
        # Use sliders instead of number inputs for easier interaction
        layout.prop(props, "ground_length", text="Base Length", slider=True)
        layout.prop(props, "input_length", text="Drive Arm", slider=True)
        layout.prop(props, "coupler_length", text="Connecting Rod", slider=True)
        layout.prop(props, "output_length", text="Output Arm", slider=True)
        
        # Visual feedback
        if (props.input_length + props.coupler_length) <= props.ground_length + props.output_length:
            layout.label(text="✅ Good proportions!", icon='CHECKMARK')
        else:
            layout.label(text="⚠️ Adjust sizes for better motion", icon='ERROR')
    
    def draw_slider_simple_params(self, layout, props):
        """Simplified slider-crank parameters."""
        layout.label(text="📏 Engine Dimensions:", icon='RULER')
        
        layout.prop(props, "crank_length", text="Crank Radius", slider=True)
        layout.prop(props, "connecting_rod_length", text="Rod Length", slider=True)
        
        # Calculate stroke for user info
        stroke = props.crank_length * 2
        layout.label(text=f"Piston Stroke: {stroke:.1f} units")


class ROBOTANIM_PT_studio_animate(Panel):
    """Simplified animation controls"""
    bl_label = "🎬 Animate"
    bl_idname = "ROBOTANIM_PT_studio_animate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_studio_main"
    
    @classmethod
    def poll(cls, context):
        return (getattr(context.scene, 'robotanim_studio_mode', False) and
                context.active_object and 
                context.active_object.type == 'ARMATURE')
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.linkage_properties
        
        # Big animation controls
        anim_box = layout.box()
        anim_box.label(text="🎬 Motion Controls", icon='PLAY')
        
        # Speed control with intuitive labels
        speed_col = anim_box.column(align=True)
        speed_col.label(text="Speed:")
        speed_col.prop(props, "input_rpm", text="RPM", slider=True)
        
        # Duration with time labels
        duration_col = anim_box.column(align=True)
        duration_col.label(text="Animation Length:")
        duration_col.prop(props, "animation_duration", text="Seconds", slider=True)
        
        layout.separator()
        
        # Visual options
        visual_box = layout.box()
        visual_box.label(text="👁️ Visualization", icon='HIDE_OFF')
        
        visual_col = visual_box.column(align=True)
        visual_col.prop(props, "show_motion_path", text="Show Motion Trail")
        visual_col.prop(props, "show_constraints", text="Show Connections")
        
        layout.separator()
        
        # Big generate button
        layout.scale_y = 2.0
        layout.operator("linkage.animate_mechanism", 
                       text="🚀 Generate Animation", 
                       icon='RENDER_ANIMATION')


class ROBOTANIM_OT_select_mechanism(Operator):
    """Select mechanism type with visual feedback"""
    bl_idname = "robotanim.select_mechanism"
    bl_label = "Select Mechanism"
    bl_options = {'REGISTER', 'UNDO'}
    
    mech_type: bpy.props.StringProperty()
    
    def execute(self, context):
        context.scene.linkage_properties.linkage_type = self.mech_type
        return {'FINISHED'}


class ROBOTANIM_OT_create_preset(Operator):
    """Create preset mechanisms for beginners"""
    bl_idname = "robotanim.create_preset"
    bl_label = "Create Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_type: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.linkage_properties
        
        if self.preset_type == 'four_bar_basic':
            # Classic four-bar proportions
            props.linkage_type = 'four_bar'
            props.ground_length = 10.0
            props.input_length = 3.0
            props.coupler_length = 8.0
            props.output_length = 5.0
            props.linkage_name = "Classic_FourBar"
            
        elif self.preset_type == 'slider_crank_engine':
            # Engine-like proportions
            props.linkage_type = 'slider_crank'
            props.crank_length = 2.0
            props.connecting_rod_length = 6.0
            props.linkage_name = "Engine_Piston"
            
        elif self.preset_type == 'robot_arm_joint':
            # Robot arm joint
            props.linkage_type = 'four_bar'
            props.ground_length = 8.0
            props.input_length = 4.0
            props.coupler_length = 6.0
            props.output_length = 3.0
            props.linkage_name = "Robot_Joint"
        
        # Auto-create the mechanism
        bpy.ops.linkage.create_mechanism()
        
        self.report({'INFO'}, f"Created {self.preset_type.replace('_', ' ').title()}!")
        return {'FINISHED'}


# Property to track studio mode
def register_studio_properties():
    """Register studio mode properties."""
    bpy.types.Scene.robotanim_studio_mode = BoolProperty(
        name="Robot Animation Studio Mode",
        description="Simplified interface mode for beginners",
        default=False
    )


def unregister_studio_properties():
    """Unregister studio mode properties."""
    del bpy.types.Scene.robotanim_studio_mode


# Classes to register
studio_classes = [
    ROBOTANIM_OT_enter_studio_mode,
    ROBOTANIM_OT_exit_studio_mode,
    ROBOTANIM_OT_select_mechanism,
    ROBOTANIM_OT_create_preset,
    ROBOTANIM_PT_studio_main,
    ROBOTANIM_PT_studio_build,
    ROBOTANIM_PT_studio_animate,
]


def register_studio_ui():
    """Register studio UI classes."""
    for cls in studio_classes:
        bpy.utils.register_class(cls)
    register_studio_properties()
    register_workspace_manager()


def unregister_studio_ui():
    """Unregister studio UI classes."""
    unregister_workspace_manager()
    unregister_studio_properties()
    for cls in reversed(studio_classes):
        bpy.utils.unregister_class(cls) 