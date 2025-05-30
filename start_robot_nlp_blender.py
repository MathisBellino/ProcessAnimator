#!/usr/bin/env python3
"""
Robot NLP Blender Launcher
Starts Blender with the Robot NLP addon pre-installed
"""

import os
import sys
import shutil
import subprocess

def main():
    print("🚀 Robot NLP Blender Launcher")
    print("="*50)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    addon_source = os.path.join(current_dir, "robot_nlp_addon.py")
    
    if not os.path.exists(addon_source):
        print("❌ Error: robot_nlp_addon.py not found!")
        print("Make sure you're running this from the correct directory.")
        return
    
    print("✅ Found Robot NLP addon")
    
    # Try to find Blender installation
    blender_paths = [
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe", 
        r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 3.6\blender.exe",
        # Add Steam installation paths
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        # Try some other common locations
        r"C:\Blender\blender.exe",
        r"C:\Tools\Blender\blender.exe",
    ]
    
    blender_exe = None
    for path in blender_paths:
        if os.path.exists(path):
            blender_exe = path
            print(f"Found Blender at: {path}")
            break
    
    # If not found, try to find it in Program Files
    if not blender_exe:
        program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
        for pf in program_files:
            blender_foundation = os.path.join(pf, "Blender Foundation")
            if os.path.exists(blender_foundation):
                for item in os.listdir(blender_foundation):
                    blender_path = os.path.join(blender_foundation, item, "blender.exe")
                    if os.path.exists(blender_path):
                        blender_exe = blender_path
                        print(f"Found Blender at: {blender_path}")
                        break
                if blender_exe:
                    break
    
    if not blender_exe:
        print("❌ Error: Blender not found automatically!")
        print("Please install Blender from: https://www.blender.org/download/")
        print("\nAlternative: Manual Setup")
        print("1. Open Blender manually")
        print("2. In Blender, go to Edit > Preferences > Add-ons")
        print("3. Click 'Install...' and select 'robot_nlp_addon.py'")
        print("4. Enable the 'Robot NLP Controller' addon")
        print("5. Look for 'Robot NLP' tab in the right sidebar")
        
        # Open the current directory in file explorer
        try:
            os.startfile(current_dir)
            print(f"\n📁 Opened folder: {current_dir}")
            print("The robot_nlp_addon.py file is ready for manual installation!")
        except:
            pass
        
        input("Press Enter when ready...")
        return
    
    print(f"✅ Found Blender: {blender_exe}")
    
    # Create a temporary startup script for Blender
    startup_script = f'''
import bpy
import sys
import os

# Add current directory to path
sys.path.insert(0, r"{current_dir}")

# Remove default cube
if "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"])

# Load and register the addon
try:
    import robot_nlp_addon
    robot_nlp_addon.register()
    print("Robot NLP addon loaded successfully!")
except Exception as e:
    print(f"Error loading addon: {{e}}")

# Set up the scene
bpy.context.scene.tool_settings.use_snap = True
'''
    
    startup_file = os.path.join(current_dir, "blender_startup.py")
    with open(startup_file, 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("✅ Created startup script")
    
    # Launch Blender
    print("🚀 Launching Blender with Robot NLP...")
    print("\nInstructions:")
    print("1. Look for 'Robot NLP' tab in the right sidebar (press N if not visible)")
    print("2. Click the quick command buttons or type your own")
    print("3. Press '🚀 Execute Command' to see the AI in action!")
    print("4. Watch as objects are created and moved based on your commands")
    
    try:
        # Launch Blender with the startup script
        subprocess.run([blender_exe, "--python", startup_file])
    except Exception as e:
        print(f"❌ Error launching Blender: {e}")
    finally:
        # Clean up
        if os.path.exists(startup_file):
            os.remove(startup_file)

if __name__ == "__main__":
    main() 