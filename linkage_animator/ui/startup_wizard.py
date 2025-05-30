#!/usr/bin/env python3
"""
Startup Wizard for Robot Animation Studio

Complete startup experience with mode selection, progress tracking,
and guided onboarding for both professional and simple users.
"""

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
import webbrowser
import os
import time


class StartupWizardProperties(PropertyGroup):
    """Properties for startup wizard state management."""
    
    wizard_active: BoolProperty(
        name="Wizard Active",
        description="Whether the startup wizard is currently active",
        default=False
    )
    
    selected_mode: EnumProperty(
        name="User Mode",
        description="Selected user experience mode",
        items=[
            ('simple', "Simple Mode", "Drag-and-drop interface for beginners"),
            ('professional', "Professional Mode", "Extended Blender tools with robot features"),
        ],
        default='simple'
    )
    
    setup_progress: IntProperty(
        name="Setup Progress",
        description="Current setup progress percentage",
        default=0,
        min=0,
        max=100
    )
    
    current_step: StringProperty(
        name="Current Step",
        description="Current setup step description",
        default="Welcome"
    )
    
    robot_catalogue_connected: BoolProperty(
        name="Robot Catalogue Connected",
        description="Whether connection to robot catalogue is established",
        default=False
    )


class ROBOTANIM_OT_startup_wizard(Operator):
    """Launch the Robot Animation Studio startup wizard"""
    bl_idname = "robotanim.startup_wizard"
    bl_label = "Robot Animation Studio Setup"
    bl_description = "Complete setup wizard for Robot Animation Studio"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        # Initialize wizard state
        context.scene.startup_wizard.wizard_active = True
        context.scene.startup_wizard.setup_progress = 0
        context.scene.startup_wizard.current_step = "Welcome"
        
        # Show as modal popup
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.startup_wizard
        
        # Main header
        header = layout.box()
        header.scale_y = 1.5
        row = header.row()
        row.alignment = 'CENTER'
        row.label(text="🤖 Robot Animation Studio", icon='ARMATURE_DATA')
        
        # Progress bar
        progress_box = layout.box()
        progress_box.label(text=f"Setup Progress: {props.setup_progress}%")
        
        # Visual progress bar
        progress_row = progress_box.row()
        progress_row.scale_y = 0.5
        for i in range(10):
            if i < (props.setup_progress // 10):
                progress_row.label(text="█", icon='NONE')
            else:
                progress_row.label(text="░", icon='NONE')
        
        progress_box.label(text=f"Current Step: {props.current_step}")
        
        layout.separator()
        
        # Mode selection
        mode_box = layout.box()
        mode_box.label(text="🎯 Choose Your Experience:", icon='SETTINGS')
        
        # Simple Mode
        simple_box = mode_box.box()
        if props.selected_mode == 'simple':
            simple_box.alert = True
        simple_row = simple_box.row()
        simple_row.scale_y = 1.5
        simple_op = simple_row.operator("robotanim.select_mode", 
                                       text="🎨 Simple Mode", 
                                       icon='RESTRICT_SELECT_OFF')
        simple_op.mode = 'simple'
        
        simple_desc = simple_box.column()
        simple_desc.label(text="✨ Drag-and-drop robot animation")
        simple_desc.label(text="✨ No Blender knowledge required")
        simple_desc.label(text="✨ Guided workflow with AI assistance")
        simple_desc.label(text="✨ Perfect for beginners and educators")
        
        # Professional Mode
        prof_box = mode_box.box()
        if props.selected_mode == 'professional':
            prof_box.alert = True
        prof_row = prof_box.row()
        prof_row.scale_y = 1.5
        prof_op = prof_row.operator("robotanim.select_mode", 
                                   text="🔧 Professional Mode", 
                                   icon='TOOL_SETTINGS')
        prof_op.mode = 'professional'
        
        prof_desc = prof_box.column()
        prof_desc.label(text="⚡ Full Blender power + robot tools")
        prof_desc.label(text="⚡ Advanced simulation features")
        prof_desc.label(text="⚡ Custom scripting and automation")
        prof_desc.label(text="⚡ Professional workflow optimization")
        
        layout.separator()
        
        # Robot catalogue section
        catalogue_box = layout.box()
        catalogue_box.label(text="🤖 Robot Catalogue", icon='WORLD')
        
        if props.robot_catalogue_connected:
            catalogue_box.label(text="✅ Connected to robot library")
            catalogue_box.operator("robotanim.browse_robots", 
                                  text="Browse Robot Models", 
                                  icon='WORLD_DATA')
        else:
            catalogue_box.label(text="🔗 Connect to download robot models")
            catalogue_box.operator("robotanim.connect_catalogue", 
                                  text="Connect to Robot Catalogue", 
                                  icon='URL')
    
    def execute(self, context):
        props = context.scene.startup_wizard
        
        if props.selected_mode and props.robot_catalogue_connected:
            # Complete setup
            bpy.ops.robotanim.complete_setup()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Please select a mode and connect to robot catalogue")
            return {'RUNNING_MODAL'}


class ROBOTANIM_OT_select_mode(Operator):
    """Select user experience mode"""
    bl_idname = "robotanim.select_mode"
    bl_label = "Select Mode"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: StringProperty()
    
    def execute(self, context):
        context.scene.startup_wizard.selected_mode = self.mode
        context.scene.startup_wizard.setup_progress = 33
        context.scene.startup_wizard.current_step = f"{self.mode.title()} Mode Selected"
        
        self.report({'INFO'}, f"Selected {self.mode.title()} Mode")
        return {'FINISHED'}


class ROBOTANIM_OT_connect_catalogue(Operator):
    """Connect to robot catalogue for model downloads"""
    bl_idname = "robotanim.connect_catalogue"
    bl_label = "Connect to Robot Catalogue"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Simulate catalogue connection with progress updates
        props = context.scene.startup_wizard
        
        # Update progress
        props.setup_progress = 66
        props.current_step = "Connecting to Robot Catalogue..."
        
        # Open robot catalogue website
        catalogue_url = "https://robot-catalogue.com/models"  # Placeholder URL
        try:
            webbrowser.open(catalogue_url)
            props.robot_catalogue_connected = True
            props.setup_progress = 90
            props.current_step = "Robot Catalogue Connected"
            self.report({'INFO'}, "Robot catalogue opened in browser")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open catalogue: {str(e)}")
        
        return {'FINISHED'}


class ROBOTANIM_OT_browse_robots(Operator):
    """Browse available robot models"""
    bl_idname = "robotanim.browse_robots"
    bl_label = "Browse Robot Models"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # This would show a browser or interface for robot selection
        self.report({'INFO'}, "Robot browser would open here")
        return {'FINISHED'}


class ROBOTANIM_OT_complete_setup(Operator):
    """Complete the startup wizard setup"""
    bl_idname = "robotanim.complete_setup"
    bl_label = "Complete Setup"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.startup_wizard
        
        # Finalize setup
        props.setup_progress = 100
        props.current_step = "Setup Complete!"
        props.wizard_active = False
        
        # Launch selected mode
        if props.selected_mode == 'simple':
            bpy.ops.robotanim.enter_simple_mode()
        else:
            bpy.ops.robotanim.enter_professional_mode()
        
        self.report({'INFO'}, f"Welcome to Robot Animation Studio - {props.selected_mode.title()} Mode!")
        return {'FINISHED'}


class ROBOTANIM_OT_enter_simple_mode(Operator):
    """Enter Simple drag-and-drop mode"""
    bl_idname = "robotanim.enter_simple_mode"
    bl_label = "Enter Simple Mode"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Configure Blender for simple mode
        self.configure_simple_interface(context)
        
        # Set scene properties
        context.scene.robotanim_studio_mode = True
        context.scene.robotanim_mode = 'simple'
        
        # Show welcome message
        self.report({'INFO'}, "Simple Mode activated - drag and drop robot animation!")
        return {'FINISHED'}
    
    def configure_simple_interface(self, context):
        """Configure Blender interface for simple mode."""
        # Hide complex UI elements
        context.preferences.view.show_developer_ui = False
        context.preferences.view.show_tooltips_python = False
        
        # Set up viewport
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.overlay.show_grid = True
                        space.show_gizmo_object_scale = False


class ROBOTANIM_OT_enter_professional_mode(Operator):
    """Enter Professional mode with extended tools"""
    bl_idname = "robotanim.enter_professional_mode"
    bl_label = "Enter Professional Mode"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Configure Blender for professional mode
        self.configure_professional_interface(context)
        
        # Set scene properties
        context.scene.robotanim_studio_mode = False
        context.scene.robotanim_mode = 'professional'
        
        # Show welcome message
        self.report({'INFO'}, "Professional Mode activated - full Blender + robot tools!")
        return {'FINISHED'}
    
    def configure_professional_interface(self, context):
        """Configure Blender interface for professional mode."""
        # Show all UI elements
        context.preferences.view.show_developer_ui = True
        context.preferences.view.show_tooltips_python = True


# Auto-launch wizard panel
class ROBOTANIM_PT_startup_launcher(Panel):
    """Startup launcher panel shown on addon activation"""
    bl_label = "🚀 Robot Animation Studio"
    bl_idname = "ROBOTANIM_PT_startup_launcher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    
    @classmethod
    def poll(cls, context):
        # Only show if wizard hasn't been completed
        props = getattr(context.scene, 'startup_wizard', None)
        return props is None or not hasattr(context.scene, 'robotanim_mode')
    
    def draw(self, context):
        layout = self.layout
        
        # Welcome message
        welcome_box = layout.box()
        welcome_box.scale_y = 1.2
        welcome_box.label(text="Welcome to Robot Animation Studio!", icon='ARMATURE_DATA')
        
        # Setup prompt
        setup_box = layout.box()
        setup_box.label(text="🎯 Ready to animate robots?")
        setup_box.label(text="Let's get you set up in 2 minutes!")
        
        # Launch wizard button
        launch_row = setup_box.row()
        launch_row.scale_y = 2.0
        launch_row.operator("robotanim.startup_wizard", 
                           text="🚀 Start Setup Wizard", 
                           icon='PLAY')


# Registration
startup_classes = [
    StartupWizardProperties,
    ROBOTANIM_OT_startup_wizard,
    ROBOTANIM_OT_select_mode,
    ROBOTANIM_OT_connect_catalogue,
    ROBOTANIM_OT_browse_robots,
    ROBOTANIM_OT_complete_setup,
    ROBOTANIM_OT_enter_simple_mode,
    ROBOTANIM_OT_enter_professional_mode,
    ROBOTANIM_PT_startup_launcher,
]


def register_startup_wizard():
    """Register startup wizard classes."""
    for cls in startup_classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    bpy.types.Scene.startup_wizard = bpy.props.PointerProperty(type=StartupWizardProperties)
    bpy.types.Scene.robotanim_mode = bpy.props.StringProperty(default="")


def unregister_startup_wizard():
    """Unregister startup wizard classes."""
    # Unregister properties
    del bpy.types.Scene.startup_wizard
    del bpy.types.Scene.robotanim_mode
    
    # Unregister classes
    for cls in reversed(startup_classes):
        bpy.utils.unregister_class(cls) 