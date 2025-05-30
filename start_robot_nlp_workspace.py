#!/usr/bin/env python3
"""
Robot NLP Workspace Launcher
Creates a completely custom Blender workspace dedicated to Robot NLP operations
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path

def find_blender_executable():
    """Find Blender executable across different platforms and versions."""
    possible_paths = [
        # Blender 4.x paths
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        # Blender 3.x paths
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.0\blender.exe",
        # Steam version
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        # Portable/other locations
        r"C:\Blender\blender.exe",
        "blender"  # In PATH
    ]
    
    print("🔍 Searching for Blender installation...")
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found Blender at: {path}")
            return path
    
    # Try PATH
    try:
        result = subprocess.run(["blender", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Found Blender in system PATH")
            return "blender"
    except:
        pass
    
    print("❌ Blender not found!")
    return None

def create_workspace_startup_script():
    """Create the startup script that will configure the Robot NLP workspace."""
    script_content = '''
import bpy
import bmesh
import os
import sys

print("🚀 Initializing Robot NLP Workspace...")

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Robot NLP specific scene setup
def setup_robot_scene():
    """Set up the optimal scene for robot NLP operations."""
    
    # Set up lighting for robot operations
    print("💡 Setting up robot lighting...")
    
    # Add key light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun_light = bpy.context.active_object
    sun_light.name = "Robot_Key_Light"
    sun_light.data.energy = 3.0
    sun_light.rotation_euler = (0.785, 0, 0.785)
    
    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-3, -3, 5))
    area_light = bpy.context.active_object
    area_light.name = "Robot_Fill_Light"
    area_light.data.energy = 1.5
    area_light.data.size = 3.0
    area_light.rotation_euler = (1.2, 0, -0.8)
    
    # Create work surface (table)
    print("📦 Creating robot work surface...")
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    table = bpy.context.active_object
    table.name = "Robot_Work_Table"
    table.scale[2] = 0.1
    
    # Create table material
    table_mat = bpy.data.materials.new(name="Robot_Table_Material")
    table_mat.use_nodes = True
    table_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.9, 1.0)
    table_mat.node_tree.nodes["Principled BSDF"].inputs[7].default_value = 0.1  # Roughness
    table.data.materials.append(table_mat)
    
    # Position camera for optimal robot viewing
    print("📷 Setting up robot camera...")
    camera = bpy.data.objects.get("Camera")
    if camera:
        camera.location = (7, -7, 5)
        camera.rotation_euler = (1.1, 0, 0.785)
    
    # Set viewport shading for best robot visualization
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Set to Material Preview mode for better visualization
                    # Check Blender version compatibility
                    try:
                        space.shading.type = 'MATERIAL_PREVIEW'
                    except TypeError:
                        # Fallback for older Blender versions
                        space.shading.type = 'MATERIAL'
                    
                    try:
                        space.shading.studio_light = 'forest.exr'
                    except:
                        pass  # Skip if not available
                        
                    space.overlay.show_floor = True
                    space.overlay.show_axis_x = True
                    space.overlay.show_axis_y = True
                    space.overlay.show_axis_z = True
                    space.overlay.grid_scale = 1.0
                    break
    
    print("✅ Robot scene setup complete!")

def create_custom_workspace():
    """Create and configure the Robot NLP workspace."""
    print("🔧 Creating Robot NLP Workspace...")
    
    # Create new workspace if it doesn't exist
    workspace_name = "Robot NLP Pro"
    try:
        if workspace_name not in bpy.data.workspaces:
            # Try to duplicate the Layout workspace as base
            if 'Layout' in bpy.data.workspaces:
                # Method for newer Blender versions
                try:
                    bpy.ops.workspace.duplicate({'workspace': bpy.data.workspaces['Layout']})
                    new_workspace = bpy.context.workspace
                    new_workspace.name = workspace_name
                except:
                    # Alternative method for older versions
                    new_workspace = bpy.data.workspaces.new(workspace_name)
            else:
                new_workspace = bpy.data.workspaces.new(workspace_name)
        else:
            new_workspace = bpy.data.workspaces[workspace_name]
        
        # Switch to the Robot NLP workspace
        bpy.context.window.workspace = new_workspace
        
        print("🎨 Configuring custom layout...")
        return new_workspace
        
    except Exception as e:
        print(f"⚠️ Workspace creation warning: {e}")
        # Use current workspace if creation fails
        return bpy.context.workspace

def setup_robot_nlp_interface():
    """Set up the Robot NLP interface in the sidebar."""
    print("🤖 Configuring Robot NLP interface...")
    
    # Make sure the 3D viewport sidebar is visible
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'UI':
                    # Force the sidebar to be visible
                    override = {'area': area, 'region': region}
                    if not region.width > 1:  # If sidebar is hidden
                        bpy.ops.screen.region_toggle(override, region_type='UI')
            break
    
    print("✅ Robot NLP interface ready!")

# Execute setup functions
setup_robot_scene()
workspace = create_custom_workspace()
setup_robot_nlp_interface()

# Set frame to 1 and prepare for robot operations
bpy.context.scene.frame_set(1)
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 250

print("🎯 Robot NLP Workspace is ready!")
print("📍 Look for 'Robot NLP' tab in the 3D viewport sidebar")
print("🚀 Ready for natural language robot commands!")

# Focus on the 3D viewport
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        bpy.context.window.cursor_set('DEFAULT')
        break
'''
    
    # Write to temporary file
    script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    script_file.write(script_content)
    script_file.close()
    
    return script_file.name

def main():
    """Main launcher function."""
    print("🤖 Robot NLP Workspace Launcher")
    print("=" * 50)
    
    # Find Blender
    blender_path = find_blender_executable()
    if not blender_path:
        print("\n❌ ERROR: Blender not found!")
        print("Please install Blender 3.2+ from https://www.blender.org/download/")
        input("Press Enter to exit...")
        return False
    
    # Check for addon files
    addon_path = "robot_nlp_workspace_addon.py"
    if not os.path.exists(addon_path):
        print(f"\n❌ ERROR: {addon_path} not found!")
        print("Make sure you're running this from the correct directory.")
        input("Press Enter to exit...")
        return False
    
    print(f"\n✅ Using Blender: {blender_path}")
    print(f"✅ Robot NLP Workspace addon: {addon_path}")
    
    # Create startup script
    print("\n🔧 Creating workspace configuration...")
    startup_script = create_workspace_startup_script()
    
    try:
        # Get absolute paths
        addon_abs = os.path.abspath(addon_path)
        
        print("\n🚀 Launching Robot NLP Workspace...")
        print("=" * 50)
        print("🎯 WHAT'S HAPPENING:")
        print("   1. Blender will open with custom Robot NLP workspace")
        print("   2. Scene will be configured for robot operations")
        print("   3. Custom panels will appear in the 3D viewport sidebar")
        print("   4. Look for 'Robot NLP' tab on the right side")
        print("   5. If sidebar not visible, press 'N' key")
        print("")
        print("🤖 DRAMATIC INTERFACE CHANGES:")
        print("   • Custom workspace tab: 'Robot NLP Pro'")
        print("   • Large command center panels")
        print("   • Custom header with robot controls")
        print("   • Professional robot status monitors")
        print("   • Dedicated animation control interface")
        print("   • Emergency stop and safety controls")
        print("")
        print("💡 QUICK START:")
        print("   • Try 'pick up the red cube'")
        print("   • Use the large quick command buttons")
        print("   • Watch AI confidence scores")
        print("   • Control animations with professional tools")
        print("=" * 50)
        
        # Build Blender command
        blender_cmd = [
            blender_path,
            "--python", startup_script,  # Run setup script first
            "--python", addon_abs,       # Then load the addon
        ]
        
        # Launch Blender
        print(f"\n🔥 Starting Blender with Robot NLP Workspace...")
        result = subprocess.run(blender_cmd)
        
        # Cleanup
        try:
            os.unlink(startup_script)
        except:
            pass
        
        if result.returncode == 0:
            print("\n✅ Robot NLP Workspace closed successfully!")
        else:
            print(f"\n⚠️ Blender exited with code {result.returncode}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Launch cancelled by user")
        return False
    except Exception as e:
        print(f"\n💥 Launch error: {e}")
        return False
    finally:
        # Cleanup temp files
        try:
            os.unlink(startup_script)
        except:
            pass

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
    sys.exit(0 if success else 1) 