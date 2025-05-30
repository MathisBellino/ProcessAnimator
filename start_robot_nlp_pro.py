#!/usr/bin/env python3
"""
Robot NLP Pro Blender Launcher
Starts Blender with the enhanced Robot NLP Pro addon
"""

import os
import sys
import shutil
import subprocess
import json

def create_blender_config():
    """Create optimal Blender configuration for Robot NLP Pro."""
    config = {
        "theme": "Dark",
        "viewport_shading": "Material Preview",
        "timeline_visible": True,
        "properties_panel": True,
        "sidebar_width": 350,
        "startup_scene": "robot_nlp_workspace"
    }
    return config

def get_blender_version_float(version_string):
    """Convert version string to float for comparison."""
    try:
        # Extract major.minor from version like "3.2" or "4.0"
        parts = version_string.split('.')
        return float(f"{parts[0]}.{parts[1]}")
    except:
        return 3.0  # Default to 3.0 if parsing fails

def main():
    print("🤖 Robot NLP Pro Blender Launcher")
    print("="*60)
    print("🚀 Enhanced AI-Powered Robot Animation Suite")
    print("="*60)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    addon_source = os.path.join(current_dir, "robot_nlp_addon_pro.py")
    
    # Check for Pro addon
    if not os.path.exists(addon_source):
        print("❌ Error: robot_nlp_addon_pro.py not found!")
        print("Make sure the Pro addon is in the current directory.")
        return
    
    print("✅ Found Robot NLP Pro addon")
    
    # Check for dependencies
    robot_animator_path = os.path.join(current_dir, 'robot_animator')
    if not os.path.exists(robot_animator_path):
        print("⚠️  Warning: robot_animator directory not found")
        print("Some AI features may not be available")
    else:
        print("✅ Found robot_animator module")
    
    # Try to find Blender installation
    blender_paths = [
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe", 
        r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.2\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 3.6\blender.exe",
        # Steam installations
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        # Other common locations
        r"C:\Blender\blender.exe",
        r"C:\Tools\Blender\blender.exe",
    ]
    
    blender_exe = None
    blender_version = "Unknown"
    
    for path in blender_paths:
        if os.path.exists(path):
            blender_exe = path
            # Extract version from path
            if "4.2" in path:
                blender_version = "4.2"
            elif "4.1" in path:
                blender_version = "4.1"
            elif "4.0" in path:
                blender_version = "4.0"
            elif "3.6" in path:
                blender_version = "3.6"
            elif "3.5" in path:
                blender_version = "3.5"
            elif "3.4" in path:
                blender_version = "3.4"
            elif "3.3" in path:
                blender_version = "3.3"
            elif "3.2" in path:
                blender_version = "3.2"
            print(f"Found Blender {blender_version} at: {path}")
            break
    
    # Auto-detect in Program Files if not found
    if not blender_exe:
        program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
        for pf in program_files:
            blender_foundation = os.path.join(pf, "Blender Foundation")
            if os.path.exists(blender_foundation):
                for item in sorted(os.listdir(blender_foundation), reverse=True):  # Get latest version
                    blender_path = os.path.join(blender_foundation, item, "blender.exe")
                    if os.path.exists(blender_path):
                        blender_exe = blender_path
                        blender_version = item.replace("Blender ", "")
                        print(f"Auto-detected Blender {blender_version} at: {blender_path}")
                        break
                if blender_exe:
                    break
    
    if not blender_exe:
        print("❌ Error: Blender not found automatically!")
        print("\n📥 Please install Blender from: https://www.blender.org/download/")
        print("   Recommended version: Blender 4.0 or newer")
        print("\n🔧 Manual Setup Instructions:")
        print("1. Open Blender manually")
        print("2. Go to Edit > Preferences > Add-ons")
        print("3. Click 'Install...' and select 'robot_nlp_addon_pro.py'")
        print("4. Enable the 'Robot NLP Controller Pro' addon")
        print("5. Look for 'Robot NLP' tab in the right sidebar (press N if hidden)")
        
        # Open current directory for manual installation
        try:
            os.startfile(current_dir)
            print(f"\n📁 Opened folder: {current_dir}")
            print("The robot_nlp_addon_pro.py file is ready for manual installation!")
        except:
            pass
        
        input("\nPress Enter when ready...")
        return
    
    print(f"✅ Using Blender {blender_version}: {blender_exe}")
    
    # Get version as float for compatibility checks
    version_float = get_blender_version_float(blender_version)
    
    # Create enhanced startup script for Robot NLP Pro with version compatibility
    startup_script = f'''
import bpy
import sys
import os
import bmesh

# Add current directory to path
current_dir = r"{current_dir}"
sys.path.insert(0, current_dir)

# Blender version for compatibility
BLENDER_VERSION = {version_float}

print("🤖 Initializing Robot NLP Pro Environment...")
print(f"🔧 Blender Version: {{BLENDER_VERSION}}")

# Remove default objects for clean start
def clean_default_scene():
    """Remove default cube, light, and camera for clean workspace."""
    objects_to_remove = ["Cube", "Light", "Camera"]
    for obj_name in objects_to_remove:
        if obj_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)

# Set up optimal workspace for robot animation
def setup_robot_workspace():
    """Configure Blender for optimal robot animation workflow."""
    
    try:
        # Switch to Layout workspace
        for workspace in bpy.data.workspaces:
            if workspace.name == "Layout":
                bpy.context.window.workspace = workspace
                break
        
        # Set viewport shading with version compatibility
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # Use appropriate shading mode based on Blender version
                        if BLENDER_VERSION >= 4.0:
                            space.shading.type = 'MATERIAL_PREVIEW'
                        elif BLENDER_VERSION >= 3.4:
                            space.shading.type = 'MATERIAL_PREVIEW'
                        else:
                            space.shading.type = 'MATERIAL'  # Fallback for older versions
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True
                        break
        
        # Add better lighting for robot visualization
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
        sun_light = bpy.context.active_object
        sun_light.name = "Robot_Sun_Light"
        sun_light.data.energy = 3
        
        # Add a ground plane
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
        ground = bpy.context.active_object
        ground.name = "Ground_Plane"
        
        # Create material for ground
        ground_mat = bpy.data.materials.new(name="Ground_Material")
        ground_mat.use_nodes = True
        if ground_mat.node_tree and "Principled BSDF" in ground_mat.node_tree.nodes:
            ground_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.3, 0.3, 0.3, 1.0)
        ground.data.materials.append(ground_mat)
        
        # Set up camera for better robot view
        bpy.ops.object.camera_add(location=(7, -7, 5))
        camera = bpy.context.active_object
        camera.name = "Robot_Camera"
        
        # Point camera at origin (with version compatibility)
        try:
            constraint = camera.constraints.new(type='TRACK_TO')
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            
            # Create empty object at origin for camera to track
            bpy.ops.object.empty_add(location=(0, 0, 1))
            target = bpy.context.active_object
            target.name = "Camera_Target"
            constraint.target = target
        except Exception as e:
            print(f"Camera constraint setup failed: {{e}}")
        
        # Set as active camera
        bpy.context.scene.camera = camera
        
        print("✅ Robot workspace setup completed")
        
    except Exception as e:
        print(f"⚠️  Workspace setup had issues: {{e}}")
        print("   Basic environment will be used instead")

# Load and register the Robot NLP Pro addon
try:
    clean_default_scene()
    setup_robot_workspace()
    
    import robot_nlp_addon_pro
    robot_nlp_addon_pro.register()
    print("✅ Robot NLP Pro addon loaded successfully!")
    
    # Show welcome message with delay
    def show_welcome():
        print("🎉 Welcome to Robot NLP Pro! Check the 'Robot NLP' tab in the sidebar.")
        return None  # Don't repeat
    
    bpy.app.timers.register(show_welcome, first_interval=2.0)
    
except Exception as e:
    print(f"❌ Error loading Robot NLP Pro addon: {{e}}")
    import traceback
    traceback.print_exc()
    print("💡 Try manual installation: Edit > Preferences > Add-ons > Install...")

# Set timeline to start at frame 1
try:
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250
except Exception as e:
    print(f"Timeline setup issue: {{e}}")

print("🚀 Robot NLP Pro is ready!")
'''
    
    startup_file = os.path.join(current_dir, "blender_startup_pro.py")
    
    try:
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        print("✅ Created enhanced startup script")
    except Exception as e:
        print(f"❌ Error creating startup script: {e}")
        return
    
    # Version-specific recommendations
    if version_float < 3.3:
        print(f"⚠️  Warning: Blender {blender_version} is quite old")
        print("   Some features may not work optimally")
        print("   Consider upgrading to Blender 3.6+ or 4.0+")
    elif version_float < 4.0:
        print(f"✅ Blender {blender_version} is compatible")
        print("   Most features will work well")
    else:
        print(f"🎯 Blender {blender_version} is optimal")
        print("   All features fully supported")
    
    # Launch Blender with enhanced configuration
    print("\n🚀 Launching Blender with Robot NLP Pro...")
    print("="*60)
    print("\n📋 FEATURES READY:")
    print("  🤖 Natural Language Robot Commands")
    print("  🎬 Real-time Animation Preview") 
    print("  ⚡ Quick Command Buttons")
    print("  📊 AI Confidence Analysis")
    print("  🎯 Safety Mode & Validation")
    print("  🔧 Advanced Settings & Controls")
    print("  🎨 Automatic Object Creation & Coloring")
    print("  ⏱️  Timeline & Keyframe Management")
    
    print("\n📖 INSTRUCTIONS:")
    print("1. Look for 'Robot NLP' tab in the right sidebar")
    print("2. If sidebar not visible, press 'N' key")
    print("3. Start with quick commands or type your own")
    print("4. Press '🚀 Execute Command' to see AI in action")
    print("5. Watch objects appear and animate based on commands")
    print("6. Use animation controls to preview and adjust")
    print("7. Check Results panel for AI analysis")
    
    print("\n💡 EXAMPLE COMMANDS:")
    print("  • 'pick up the red cube and place it on the table'")
    print("  • 'grab the blue sphere and move it to the corner'") 
    print("  • 'organize all objects by color'")
    print("  • 'rotate the cylinder 90 degrees'")
    print("  • 'move the robot to home position'")
    
    # Skip actual launch if --test flag is provided
    if "--test" in sys.argv:
        print("\n🧪 Test mode - skipping Blender launch")
        return
    
    try:
        # Launch Blender with the enhanced startup script
        cmd = [blender_exe, "--python", startup_file]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n⏹️  Launch cancelled by user")
    except Exception as e:
        print(f"❌ Error launching Blender: {e}")
        print("\nTrying alternative launch method...")
        try:
            # Alternative launch without startup script
            subprocess.run([blender_exe])
        except Exception as e2:
            print(f"❌ Alternative launch failed: {e2}")
    finally:
        # Clean up startup file
        try:
            if os.path.exists(startup_file):
                os.remove(startup_file)
                print("🧹 Cleanup completed")
        except:
            pass

def show_system_info():
    """Display system information and requirements."""
    print("\n💻 SYSTEM REQUIREMENTS:")
    print("  • Blender 3.2+ (4.0+ recommended)")
    print("  • Python 3.8+")
    print("  • 4GB+ RAM")
    print("  • OpenGL 3.3+ compatible GPU")
    
    print("\n🔍 TROUBLESHOOTING:")
    print("  • If addon doesn't load: Check Blender console for errors")
    print("  • If AI unavailable: Install dependencies with pip")
    print("  • If objects don't appear: Check Blender outliner")
    print("  • If animations are slow: Reduce complexity or frame count")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        show_system_info()
        input("Press Enter to exit...") 