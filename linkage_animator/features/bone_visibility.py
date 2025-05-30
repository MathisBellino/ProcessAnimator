#!/usr/bin/env python3
"""
Bone Visibility Toggle System

One-click toggle to show only bones/armatures and hide all mesh objects.
Perfect for robot joint visualization and teaching mode.
"""

import bpy
from bpy.types import Operator, Panel
from bpy.props import BoolProperty
import logging

logger = logging.getLogger(__name__)


class BoneVisibilityManager:
    """
    Manager for toggling between mesh and bone-only visibility modes.
    """
    
    def __init__(self):
        self.stored_visibility = {}
        self.bone_only_mode = False
        
    def toggle_bone_only_mode(self, context):
        """Toggle between bone-only and normal visibility modes."""
        if not self.bone_only_mode:
            self.enter_bone_only_mode(context)
        else:
            self.exit_bone_only_mode(context)
        
        return self.bone_only_mode
    
    def enter_bone_only_mode(self, context):
        """Enter bone-only visualization mode."""
        self.stored_visibility.clear()
        
        # Store current visibility and hide mesh objects
        for obj in context.scene.objects:
            # Store current visibility state
            self.stored_visibility[obj.name] = {
                'hide_viewport': obj.hide_viewport,
                'hide_render': obj.hide_render,
                'display_type': obj.display_type,
                'show_in_front': obj.show_in_front
            }
            
            if obj.type == 'MESH':
                # Hide mesh objects
                obj.hide_viewport = True
                
            elif obj.type == 'ARMATURE':
                # Show armatures and enhance bone visibility
                obj.hide_viewport = False
                obj.display_type = 'WIRE'
                obj.show_in_front = True
                
                # Set armature display settings for better visibility
                if obj.data:
                    obj.data.display_type = 'STICK'
                    obj.data.show_names = True
                    obj.data.show_bone_custom_shapes = False
                    obj.data.show_axes = True
        
        # Adjust viewport shading for better bone visibility
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # Store current shading mode
                        if 'viewport_shading' not in self.stored_visibility:
                            self.stored_visibility['viewport_shading'] = {
                                'type': space.shading.type,
                                'show_xray': space.shading.show_xray,
                                'xray_alpha': space.shading.xray_alpha if hasattr(space.shading, 'xray_alpha') else 0.5
                            }
                        
                        # Set optimal shading for bone visualization
                        space.shading.type = 'SOLID'
                        space.shading.show_xray = True
                        if hasattr(space.shading, 'xray_alpha'):
                            space.shading.xray_alpha = 0.8
        
        self.bone_only_mode = True
        logger.info("Entered bone-only visualization mode")
    
    def exit_bone_only_mode(self, context):
        """Exit bone-only mode and restore original visibility."""
        # Restore object visibility
        for obj in context.scene.objects:
            if obj.name in self.stored_visibility:
                stored = self.stored_visibility[obj.name]
                obj.hide_viewport = stored['hide_viewport']
                obj.hide_render = stored['hide_render']
                obj.display_type = stored['display_type']
                obj.show_in_front = stored['show_in_front']
                
                # Restore armature settings
                if obj.type == 'ARMATURE' and obj.data:
                    obj.data.display_type = 'OCTAHEDRAL'  # Default
                    obj.data.show_names = False
                    obj.data.show_bone_custom_shapes = True
                    obj.data.show_axes = False
        
        # Restore viewport shading
        if 'viewport_shading' in self.stored_visibility:
            shading_data = self.stored_visibility['viewport_shading']
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.type = shading_data['type']
                            space.shading.show_xray = shading_data['show_xray']
                            if hasattr(space.shading, 'xray_alpha'):
                                space.shading.xray_alpha = shading_data['xray_alpha']
        
        self.bone_only_mode = False
        self.stored_visibility.clear()
        logger.info("Exited bone-only visualization mode")
    
    def focus_on_armature(self, context, armature_obj):
        """Focus viewport on specific armature."""
        if armature_obj and armature_obj.type == 'ARMATURE':
            # Select and make active
            bpy.ops.object.select_all(action='DESELECT')
            armature_obj.select_set(True)
            context.view_layer.objects.active = armature_obj
            
            # Frame the armature in view
            bpy.ops.view3d.view_selected()
            
            logger.info(f"Focused on armature: {armature_obj.name}")
    
    def enhance_bone_visualization(self, context):
        """Apply enhanced settings for bone visualization."""
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE' and obj.data:
                armature = obj.data
                
                # Enhanced bone display settings
                armature.display_type = 'STICK'
                armature.show_names = True
                armature.show_axes = True
                armature.show_bone_custom_shapes = False
                
                # Color coding for different bone types
                if hasattr(armature, 'bones'):
                    for bone in armature.bones:
                        # Color code bones by hierarchy level
                        if not bone.parent:
                            # Root bones - red
                            bone.color.palette = 'THEME01'
                        elif len([b for b in armature.bones if b.parent == bone]) == 0:
                            # Leaf bones (end effectors) - green
                            bone.color.palette = 'THEME03'
                        else:
                            # Middle bones - blue
                            bone.color.palette = 'THEME04'
                        
                        bone.color.custom = bone.color
    
    def create_bone_analysis_overlay(self, context):
        """Create overlay information for bone analysis."""
        # This would create text overlays showing bone information
        # For now, we'll just log the analysis
        bone_count = 0
        armature_count = 0
        
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                armature_count += 1
                if obj.data:
                    bone_count += len(obj.data.bones)
        
        logger.info(f"Scene analysis: {armature_count} armatures, {bone_count} total bones")
        return {'armatures': armature_count, 'bones': bone_count}


class ROBOTANIM_OT_toggle_bone_visibility(Operator):
    """Toggle bone-only visibility mode"""
    bl_idname = "robotanim.toggle_bone_visibility"
    bl_label = "Toggle Bone Only Mode"
    bl_description = "Show only bones/armatures and hide mesh objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get or create visibility manager
        if not hasattr(bpy.types.Scene, '_bone_visibility_manager'):
            bpy.types.Scene._bone_visibility_manager = BoneVisibilityManager()
        
        manager = bpy.types.Scene._bone_visibility_manager
        
        # Toggle mode
        new_mode = manager.toggle_bone_only_mode(context)
        
        if new_mode:
            self.report({'INFO'}, "Entered bone-only visualization mode")
        else:
            self.report({'INFO'}, "Returned to normal visibility mode")
        
        # Update scene property for UI feedback
        context.scene['bone_only_mode'] = new_mode
        
        return {'FINISHED'}


class ROBOTANIM_OT_focus_armature(Operator):
    """Focus on selected armature"""
    bl_idname = "robotanim.focus_armature"
    bl_label = "Focus on Armature"
    bl_description = "Focus viewport on selected armature"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'ARMATURE':
            # Find first armature in scene
            for obj in context.scene.objects:
                if obj.type == 'ARMATURE':
                    active_obj = obj
                    break
            
            if not active_obj:
                self.report({'ERROR'}, "No armature found in scene")
                return {'CANCELLED'}
        
        # Get visibility manager
        if not hasattr(bpy.types.Scene, '_bone_visibility_manager'):
            bpy.types.Scene._bone_visibility_manager = BoneVisibilityManager()
        
        manager = bpy.types.Scene._bone_visibility_manager
        manager.focus_on_armature(context, active_obj)
        
        self.report({'INFO'}, f"Focused on armature: {active_obj.name}")
        return {'FINISHED'}


class ROBOTANIM_OT_enhance_bone_visualization(Operator):
    """Enhance bone visualization settings"""
    bl_idname = "robotanim.enhance_bone_visualization"
    bl_label = "Enhance Bone Display"
    bl_description = "Apply enhanced settings for better bone visualization"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get visibility manager
        if not hasattr(bpy.types.Scene, '_bone_visibility_manager'):
            bpy.types.Scene._bone_visibility_manager = BoneVisibilityManager()
        
        manager = bpy.types.Scene._bone_visibility_manager
        manager.enhance_bone_visualization(context)
        
        # Create analysis
        analysis = manager.create_bone_analysis_overlay(context)
        
        self.report({'INFO'}, 
                   f"Enhanced visualization for {analysis['armatures']} armatures, {analysis['bones']} bones")
        return {'FINISHED'}


class ROBOTANIM_OT_bone_teaching_mode(Operator):
    """Enable bone teaching mode with labels and highlights"""
    bl_idname = "robotanim.bone_teaching_mode"
    bl_label = "Teaching Mode"
    bl_description = "Enable educational bone visualization with labels and highlights"
    bl_options = {'REGISTER', 'UNDO'}
    
    teaching_mode: BoolProperty(
        name="Teaching Mode",
        description="Enable teaching mode visualization",
        default=False
    )
    
    def execute(self, context):
        # Get visibility manager
        if not hasattr(bpy.types.Scene, '_bone_visibility_manager'):
            bpy.types.Scene._bone_visibility_manager = BoneVisibilityManager()
        
        manager = bpy.types.Scene._bone_visibility_manager
        
        if not manager.bone_only_mode:
            # Enter bone-only mode first
            manager.enter_bone_only_mode(context)
        
        # Apply teaching enhancements
        manager.enhance_bone_visualization(context)
        
        # Enable additional teaching features
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE' and obj.data:
                armature = obj.data
                armature.show_names = True
                armature.show_axes = True
                armature.show_bone_custom_shapes = False
                
                # Set pose mode for better interaction
                context.view_layer.objects.active = obj
                if context.mode != 'POSE':
                    bpy.ops.object.mode_set(mode='POSE')
        
        context.scene['teaching_mode'] = True
        self.report({'INFO'}, "Teaching mode enabled - bone names and axes visible")
        return {'FINISHED'}


# Panel for bone visibility controls
class ROBOTANIM_PT_bone_visibility(Panel):
    """Panel for bone visibility controls"""
    bl_label = "👁️ Bone Visibility"
    bl_idname = "ROBOTANIM_PT_bone_visibility"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    def draw(self, context):
        layout = self.layout
        
        # Check current mode
        bone_only_mode = context.scene.get('bone_only_mode', False)
        teaching_mode = context.scene.get('teaching_mode', False)
        
        # Header
        header_box = layout.box()
        header_box.label(text="Bone & Joint Visualization", icon='BONE_DATA')
        
        # Status indicator
        status_box = layout.box()
        if bone_only_mode:
            status_box.alert = False
            status_box.label(text="🦴 Bone-Only Mode Active", icon='VISIBLE_IPO_ON')
        else:
            status_box.label(text="👁️ Normal Visibility", icon='VISIBLE_IPO_OFF')
        
        if teaching_mode:
            status_box.label(text="🎓 Teaching Mode Enabled", icon='INFO')
        
        layout.separator()
        
        # Main controls
        controls_box = layout.box()
        controls_box.label(text="⚡ Quick Controls:", icon='SETTINGS')
        
        # Toggle bone-only mode (main feature)
        if bone_only_mode:
            controls_box.operator("robotanim.toggle_bone_visibility", 
                                 text="Show All Objects", 
                                 icon='MESH_CUBE')
        else:
            controls_box.operator("robotanim.toggle_bone_visibility", 
                                 text="Show Only Bones", 
                                 icon='BONE_DATA')
        
        # Additional controls
        controls_box.operator("robotanim.focus_armature", 
                            text="Focus on Robot", 
                            icon='ZOOM_SELECTED')
        
        layout.separator()
        
        # Enhancement controls
        enhance_box = layout.box()
        enhance_box.label(text="🔧 Enhancement Tools:", icon='MODIFIER_ON')
        
        enhance_box.operator("robotanim.enhance_bone_visualization", 
                           text="Enhance Bone Display", 
                           icon='OUTLINER_OB_ARMATURE')
        
        enhance_box.operator("robotanim.bone_teaching_mode", 
                           text="Teaching Mode", 
                           icon='INFO')
        
        # Information
        info_box = layout.box()
        info_box.label(text="ℹ️ Information:", icon='QUESTION')
        
        # Count armatures and bones
        armature_count = 0
        bone_count = 0
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                armature_count += 1
                if obj.data:
                    bone_count += len(obj.data.bones)
        
        info_box.label(text=f"Robots: {armature_count}")
        info_box.label(text=f"Total Joints: {bone_count}")
        
        # Tips
        tips_box = layout.box()
        tips_box.label(text="💡 Tips:", icon='LIGHTBULB')
        tips_box.label(text="• Use bone-only mode for joint analysis")
        tips_box.label(text="• Teaching mode shows joint names")
        tips_box.label(text="• Focus to center view on robot")


# Registration
bone_visibility_classes = [
    ROBOTANIM_OT_toggle_bone_visibility,
    ROBOTANIM_OT_focus_armature,
    ROBOTANIM_OT_enhance_bone_visualization,
    ROBOTANIM_OT_bone_teaching_mode,
    ROBOTANIM_PT_bone_visibility,
]


def register_bone_visibility():
    """Register bone visibility classes."""
    for cls in bone_visibility_classes:
        bpy.utils.register_class(cls)


def unregister_bone_visibility():
    """Unregister bone visibility classes."""
    # Clean up visibility manager
    if hasattr(bpy.types.Scene, '_bone_visibility_manager'):
        delattr(bpy.types.Scene, '_bone_visibility_manager')
    
    # Unregister classes
    for cls in reversed(bone_visibility_classes):
        bpy.utils.unregister_class(cls) 