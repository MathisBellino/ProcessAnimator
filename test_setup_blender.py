#!/usr/bin/env python3
"""
Test Setup Script for ProcessAnimator in Blender

This script sets up a proper Blender environment for testing ProcessAnimator:
- Clears default scene
- Sets up camera and lighting
- Configures UI layout  
- Loads ProcessAnimator addon
- Creates test objects

Run this in Blender's scripting workspace.
"""

import bpy
import bmesh
import os
import sys
from mathutils import Vector, Euler

def clear_default_scene():
    """Clear the default Blender scene."""
    print("🧹 Clearing default scene...")
    
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    
    # Delete all objects
    bpy.ops.object.delete(use_global=False)
    
    # Clear materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    print("✅ Scene cleared")

def setup_camera_and_viewport():
    """Set up camera for optimal robot viewing."""
    print("📷 Setting up camera and viewport...")
    
    # Add camera
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "ProcessAnimator_Camera"
    
    # Point camera at origin
    camera.rotation_euler = Euler((1.1, 0, 0.785), 'XYZ')
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    # Setup viewport for good robot viewing
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Set viewport shading
                    space.shading.type = 'MATERIAL'
                    space.shading.use_scene_lights = True
                    space.shading.use_scene_world = True
                    
                    # Set camera view
                    space.region_3d.view_perspective = 'CAMERA'
                    break
    
    print("✅ Camera and viewport configured")

def setup_lighting():
    """Set up proper lighting for robot visualization."""
    print("💡 Setting up lighting...")
    
    # Add key light
    bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = 3
    key_light.rotation_euler = Euler((0.3, 0.3, 0), 'XYZ')
    
    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-3, -3, 4))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 1
    fill_light.data.size = 5
    
    # Set world background
    world = bpy.context.scene.world
    if world.use_nodes:
        bg_node = world.node_tree.nodes.get('Background')
        if bg_node:
            bg_node.inputs[0].default_value = (0.05, 0.05, 0.1, 1.0)  # Dark blue
            bg_node.inputs[1].default_value = 0.1  # Low strength
    
    print("✅ Lighting configured")

def create_ground_plane():
    """Create a ground plane for reference."""
    print("🏠 Creating ground plane...")
    
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground_Plane"
    
    # Create ground material
    mat = bpy.data.materials.new(name="Ground_Material")
    mat.use_nodes = True
    
    # Setup material nodes
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # Set material properties
    bsdf.inputs[0].default_value = (0.3, 0.3, 0.3, 1.0)  # Gray
    bsdf.inputs[7].default_value = 0.8  # Roughness
    bsdf.inputs[12].default_value = 0.0  # Specular
    
    # Connect nodes
    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
    
    # Apply material
    ground.data.materials.append(mat)
    
    print("✅ Ground plane created")

def create_test_objects():
    """Create some test objects for scaling and animation."""
    print("🔧 Creating test objects...")
    
    # Create a simple assembly to test with
    objects_created = []
    
    # Base component
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    base = bpy.context.active_object
    base.name = "Test_Base"
    objects_created.append(base.name)
    
    # Component 1 - could be a "screw" for scaling reference
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.2, location=(0.3, 0.3, 0.1))
    screw = bpy.context.active_object
    screw.name = "Test_Screw_5mm"  # This will be our 5mm reference
    objects_created.append(screw.name)
    
    # Component 2 - larger part
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(-0.4, 0.4, 0.25))
    part = bpy.context.active_object
    part.name = "Test_Component"
    objects_created.append(part.name)
    
    # Create a collection for test objects
    test_collection = bpy.data.collections.new("Test_Assembly")
    bpy.context.scene.collection.children.link(test_collection)
    
    # Move objects to collection
    for obj_name in objects_created:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            bpy.context.scene.collection.objects.unlink(obj)
            test_collection.objects.link(obj)
    
    print(f"✅ Created test objects: {objects_created}")

def setup_ui_layout():
    """Configure Blender UI layout for ProcessAnimator testing."""
    print("🖥️ Setting up UI layout...")
    
    # Switch to Layout workspace if available
    for workspace in bpy.data.workspaces:
        if workspace.name == 'Layout':
            bpy.context.window.workspace = workspace
            break
    
    # Ensure sidebar is visible
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.show_region_ui = True  # Show N-panel
                    break
    
    print("✅ UI layout configured")

def load_processanimator_addon():
    """Load and enable ProcessAnimator addon."""
    print("🤖 Loading ProcessAnimator addon...")
    
    try:
        # Try to enable the addon if it's already installed
        bpy.ops.preferences.addon_enable(module="robot_animator")
        print("✅ ProcessAnimator addon enabled")
        return True
    except:
        print("⚠️ ProcessAnimator addon not found in Blender addons")
        print("📋 Manual installation required:")
        print("   1. Go to Edit > Preferences > Add-ons")
        print("   2. Click 'Install...'")
        print("   3. Select the robot_animator folder")
        print("   4. Enable 'ProcessAnimator - Hyper-Intelligent Robot Animation'")
        return False

def add_debug_info():
    """Add helpful debug information to the scene."""
    print("📊 Adding debug information...")
    
    # Create text object with instructions
    bpy.ops.object.text_add(location=(0, -4, 2))
    text_obj = bpy.context.active_object
    text_obj.name = "Debug_Instructions"
    
    text_obj.data.body = """ProcessAnimator Test Setup
    
Test Steps:
1. Look for ProcessAnimator panel in sidebar (N key)
2. Try: "UR10 picks test screw and moves to base"
3. Use "Test_Screw_5mm" as 5mm reference for scaling
4. Generate wireframe preview first
5. Check dashboard for AI confidence

Camera Controls:
- Middle Mouse: Rotate view
- Shift+Middle Mouse: Pan
- Scroll: Zoom"""
    
    # Make text face camera
    text_obj.rotation_euler = Euler((1.57, 0, 0), 'XYZ')
    
    print("✅ Debug information added")

def main():
    """Main setup function."""
    print("\n🚀 ProcessAnimator Test Setup Starting...")
    print("=" * 50)
    
    # Setup scene
    clear_default_scene()
    setup_camera_and_viewport()
    setup_lighting()
    create_ground_plane()
    create_test_objects()
    setup_ui_layout()
    
    # Try to load addon
    addon_loaded = load_processanimator_addon()
    
    # Add debug info
    add_debug_info()
    
    # Final setup
    bpy.context.view_layer.update()
    
    print("=" * 50)
    print("🎉 ProcessAnimator Test Setup Complete!")
    print("\n📋 Next Steps:")
    
    if addon_loaded:
        print("✅ ProcessAnimator loaded - check sidebar for panel")
        print("🧪 Test with: 'UR10 picks test screw and moves to base'")
        print("📏 Use 'Test_Screw_5mm' as 5mm scaling reference")
    else:
        print("⚠️ Manually install ProcessAnimator addon first")
        print("📁 Addon location: robot_animator folder")
    
    print("🎬 Press Tab to switch to edit mode")
    print("👀 Press Numpad 0 for camera view")
    print("🔧 Press N to toggle sidebar")
    
    # Set frame to 1
    bpy.context.scene.frame_set(1)

if __name__ == "__main__":
    main() 