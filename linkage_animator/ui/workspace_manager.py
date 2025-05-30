#!/usr/bin/env python3
"""
Workspace Manager for Robot Animation Studio

Creates custom workspaces and manages UI visibility for beginner-friendly experience.
"""

import bpy


class WorkspaceManager:
    """Manages custom workspaces and UI visibility."""
    
    def __init__(self):
        self.original_ui_state = {}
    
    def create_robot_studio_workspace(self):
        """Create a custom workspace optimized for robot animation."""
        
        # Check if workspace already exists
        if "Robot Animation Studio" in bpy.data.workspaces:
            return bpy.data.workspaces["Robot Animation Studio"]
        
        # Create new workspace based on Animation workspace
        if "Animation" in bpy.data.workspaces:
            base_workspace = bpy.data.workspaces["Animation"]
        else:
            base_workspace = bpy.data.workspaces[0]  # Use first available
        
        # Duplicate the workspace
        new_workspace = base_workspace.copy()
        new_workspace.name = "Robot Animation Studio"
        
        # Configure the workspace
        self.configure_studio_workspace(new_workspace)
        
        return new_workspace
    
    def configure_studio_workspace(self, workspace):
        """Configure workspace for robot animation studio."""
        
        # Switch to the workspace to configure it
        bpy.context.window.workspace = workspace
        
        # Configure each screen in the workspace
        for screen in workspace.screens:
            self.configure_screen_for_studio(screen)
    
    def configure_screen_for_studio(self, screen):
        """Configure a screen for studio mode."""
        
        for area in screen.areas:
            # Configure 3D Viewport
            if area.type == 'VIEW_3D':
                self.configure_3d_viewport(area)
            
            # Configure Timeline
            elif area.type == 'TIMELINE':
                self.configure_timeline(area)
            
            # Configure Properties panel
            elif area.type == 'PROPERTIES':
                # Keep properties but simplify
                pass
            
            # Hide complex editors for beginners
            elif area.type in ['TEXT_EDITOR', 'CONSOLE', 'INFO']:
                # Could change these to simpler editors
                pass
    
    def configure_3d_viewport(self, area):
        """Configure 3D viewport for robot animation."""
        
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                # Set optimal shading
                space.shading.type = 'SOLID'
                space.shading.light = 'STUDIO'
                space.shading.studio_light = 'forest.exr'
                
                # Show helpful overlays
                space.overlay.show_grid = True
                space.overlay.show_axis_x = True
                space.overlay.show_axis_y = True
                space.overlay.show_axis_z = True
                space.overlay.show_bone_origins = True
                space.overlay.show_armature_names = True
                
                # Configure gizmos
                space.show_gizmo = True
                space.show_gizmo_object_translate = True
                space.show_gizmo_object_rotate = True
                space.show_gizmo_object_scale = False  # Hide scale for simplicity
                
                # Set camera view
                space.region_3d.view_perspective = 'PERSP'
    
    def configure_timeline(self, area):
        """Configure timeline for animation."""
        
        for space in area.spaces:
            if space.type == 'TIMELINE':
                # Show important timeline features
                space.show_seconds = True
                space.show_markers = True
    
    def enter_beginner_mode(self, context):
        """Hide complex UI elements for beginners."""
        
        # Store original state
        self.original_ui_state = {
            'show_tooltips_python': context.preferences.view.show_tooltips_python,
            'show_developer_ui': context.preferences.view.show_developer_ui,
        }
        
        # Simplify UI
        context.preferences.view.show_tooltips_python = False
        context.preferences.view.show_developer_ui = False
        
        # Hide complex panels in Properties editor
        self.hide_complex_properties(context)
    
    def exit_beginner_mode(self, context):
        """Restore complex UI elements."""
        
        if self.original_ui_state:
            # Restore original settings
            context.preferences.view.show_tooltips_python = self.original_ui_state.get('show_tooltips_python', True)
            context.preferences.view.show_developer_ui = self.original_ui_state.get('show_developer_ui', False)
    
    def hide_complex_properties(self, context):
        """Hide complex properties panels."""
        
        # This would involve customizing which property panels are shown
        # For now, we'll handle this through our custom UI panels
        pass
    
    def setup_studio_theme(self):
        """Set up a beginner-friendly theme."""
        
        # Could create/apply a custom theme here
        # For now, use default but could customize colors
        pass


# Operator to switch workspaces
class ROBOTANIM_OT_switch_workspace(bpy.types.Operator):
    """Switch to Robot Animation Studio workspace"""
    bl_idname = "robotanim.switch_workspace"
    bl_label = "Switch to Studio Workspace"
    bl_description = "Switch to optimized robot animation workspace"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        manager = WorkspaceManager()
        
        # Create or get the studio workspace
        studio_workspace = manager.create_robot_studio_workspace()
        
        # Switch to it
        context.window.workspace = studio_workspace
        
        # Enter beginner mode
        manager.enter_beginner_mode(context)
        
        self.report({'INFO'}, "Switched to Robot Animation Studio workspace")
        return {'FINISHED'}


# Function to register workspace components
def register_workspace_manager():
    """Register workspace manager components."""
    bpy.utils.register_class(ROBOTANIM_OT_switch_workspace)


def unregister_workspace_manager():
    """Unregister workspace manager components."""
    bpy.utils.unregister_class(ROBOTANIM_OT_switch_workspace)


if __name__ == "__main__":
    # Test the workspace manager
    manager = WorkspaceManager()
    print("Workspace manager created") 