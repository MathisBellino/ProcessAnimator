#!/usr/bin/env python3
"""
Blender Development Script - Run this directly in Blender's Text Editor

This script allows you to develop and test your linkage animator 
directly inside Blender without external files.
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Euler
import math
import logging

# Clear existing objects for testing
def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

# Simple Four-Bar Linkage Implementation for Testing
class SimpleFourBarLinkage:
    """Simplified four-bar linkage for testing in Blender."""
    
    def __init__(self, ground_length, input_length, coupler_length, output_length):
        self.ground_length = ground_length
        self.input_length = input_length
        self.coupler_length = coupler_length
        self.output_length = output_length
    
    def solve_positions(self, input_angle):
        """Solve four-bar linkage positions."""
        try:
            # Ground link positions
            A = Vector((0, 0, 0))  # Ground start
            B = Vector((self.ground_length, 0, 0))  # Ground end
            
            # Input link position
            C = A + self.input_length * Vector((math.cos(input_angle), math.sin(input_angle), 0))
            
            # Solve for output link angle using geometry
            BC = C - B
            BC_length = BC.length
            
            # Check if solution exists
            if BC_length > (self.coupler_length + self.output_length):
                return None
            if BC_length < abs(self.coupler_length - self.output_length):
                return None
            
            # Calculate output angle
            gamma = math.atan2(BC.y, BC.x)
            cos_alpha = (self.output_length**2 + BC_length**2 - self.coupler_length**2) / (2 * self.output_length * BC_length)
            cos_alpha = max(-1, min(1, cos_alpha))
            alpha = math.acos(cos_alpha)
            
            output_angle = gamma + alpha
            D = B + self.output_length * Vector((math.cos(output_angle), math.sin(output_angle), 0))
            
            return {
                'A': A, 'B': B, 'C': C, 'D': D,
                'input_angle': input_angle,
                'output_angle': output_angle
            }
            
        except:
            return None

def create_linkage_armature(linkage_config):
    """Create armature for four-bar linkage."""
    
    # Create linkage
    linkage = SimpleFourBarLinkage(
        linkage_config['ground_length'],
        linkage_config['input_length'],
        linkage_config['coupler_length'],
        linkage_config['output_length']
    )
    
    # Solve initial position
    positions = linkage.solve_positions(0)
    if not positions:
        print("❌ Invalid linkage configuration")
        return None
    
    # Create armature
    bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
    armature_obj = bpy.context.active_object
    armature_obj.name = linkage_config['name']
    armature_data = armature_obj.data
    
    # Remove default bone
    armature_data.edit_bones.remove(armature_data.edit_bones[0])
    
    # Create bones
    # Ground link
    ground_bone = armature_data.edit_bones.new('ground_link')
    ground_bone.head = positions['A']
    ground_bone.tail = positions['B']
    
    # Input link
    input_bone = armature_data.edit_bones.new('input_link')
    input_bone.head = positions['A']
    input_bone.tail = positions['C']
    
    # Coupler link
    coupler_bone = armature_data.edit_bones.new('coupler_link')
    coupler_bone.head = positions['C']
    coupler_bone.tail = positions['D']
    
    # Output link
    output_bone = armature_data.edit_bones.new('output_link')
    output_bone.head = positions['D']
    output_bone.tail = positions['B']
    
    # Set parent relationships
    coupler_bone.parent = input_bone
    coupler_bone.use_connect = False
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Store linkage data
    armature_obj['linkage'] = linkage
    armature_obj['linkage_config'] = linkage_config
    
    print(f"✅ Created {linkage_config['name']} armature")
    return armature_obj

def animate_linkage(armature_obj, duration_frames=120):
    """Create animation for the linkage."""
    
    if 'linkage' not in armature_obj:
        print("❌ Not a linkage armature")
        return
    
    linkage = armature_obj['linkage']
    
    # Switch to pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    
    # Clear existing animation
    if armature_obj.animation_data:
        armature_obj.animation_data_clear()
    
    # Generate keyframes
    for frame in range(1, duration_frames + 1):
        bpy.context.scene.frame_set(frame)
        
        # Calculate input angle
        input_angle = (frame - 1) / duration_frames * 2 * math.pi
        
        # Solve positions
        positions = linkage.solve_positions(input_angle)
        if not positions:
            continue
        
        # Set bone rotations
        pose_bones = armature_obj.pose.bones
        
        # Input link rotation
        if 'input_link' in pose_bones:
            pose_bones['input_link'].rotation_euler = Euler((0, 0, input_angle), 'XYZ')
            pose_bones['input_link'].keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Output link rotation  
        if 'output_link' in pose_bones:
            pose_bones['output_link'].rotation_euler = Euler((0, 0, positions['output_angle']), 'XYZ')
            pose_bones['output_link'].keyframe_insert(data_path="rotation_euler", frame=frame)
    
    # Set scene frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = duration_frames
    bpy.context.scene.frame_current = 1
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"✅ Animation created: {duration_frames} frames")

# ==========================================
# MAIN DEVELOPMENT TESTING AREA
# ==========================================

def main():
    """Main function for testing linkage creation and animation."""
    
    print("🚀 Starting Linkage Development Test")
    print("=" * 40)
    
    # Clear the scene
    clear_scene()
    
    # Test configuration
    linkage_config = {
        'name': 'DevTest_FourBar',
        'ground_length': 10.0,
        'input_length': 3.0,
        'coupler_length': 8.0,
        'output_length': 5.0
    }
    
    # Create the linkage
    armature = create_linkage_armature(linkage_config)
    
    if armature:
        # Create animation
        animate_linkage(armature, duration_frames=120)
        
        # Set viewport to see the animation
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.show_gizmo = True
                        space.show_gizmo_object_translate = True
                        space.show_gizmo_object_rotate = True
        
        print("\n🎉 Test Complete!")
        print("🎬 Press SPACE to play animation")
        print("🔄 Modify this script and run again to test changes")
        
    else:
        print("❌ Test failed")

# ==========================================
# QUICK DEVELOPMENT HELPERS
# ==========================================

def quick_test_slider_crank():
    """Quick test for slider-crank mechanism."""
    print("🔧 Testing Slider-Crank Mechanism")
    # Add your slider-crank test code here
    pass

def reload_addon():
    """Reload the linkage animator addon if installed."""
    import importlib
    import sys
    
    addon_name = "linkage_animator"
    
    # Disable addon
    if addon_name in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_disable(module=addon_name)
    
    # Reload modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(addon_name):
            importlib.reload(sys.modules[module_name])
    
    # Re-enable addon
    bpy.ops.preferences.addon_enable(module=addon_name)
    print("✅ Addon reloaded!")

# ==========================================
# RUN THE TEST
# ==========================================

if __name__ == "__main__":
    main()

# Uncomment these for quick testing:
# quick_test_slider_crank()
# reload_addon() 