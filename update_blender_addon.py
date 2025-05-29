#!/usr/bin/env python3
"""
Development Helper Script for Blender Addon

Quick update script for development workflow.
Run this script to instantly update your addon in Blender.
"""

import os
import shutil
import sys
from pathlib import Path

def update_blender_addon():
    """Update the addon in Blender's addons directory."""
    
    # Source directory (current project)
    source_dir = Path(__file__).parent / "linkage_animator"
    
    # Blender addon directory
    blender_addons_dir = Path.home() / "AppData/Roaming/Blender Foundation/Blender"
    
    # Find the most recent Blender version
    blender_versions = []
    if blender_addons_dir.exists():
        for version_dir in blender_addons_dir.iterdir():
            if version_dir.is_dir() and version_dir.name.replace('.', '').isdigit():
                blender_versions.append(version_dir)
    
    if not blender_versions:
        print("❌ No Blender installation found!")
        return False
    
    # Use the most recent version
    latest_version = sorted(blender_versions, key=lambda x: x.name)[-1]
    target_dir = latest_version / "scripts/addons/linkage_animator"
    
    print(f"🎯 Updating addon from:")
    print(f"   Source: {source_dir}")
    print(f"   Target: {target_dir}")
    
    try:
        # Remove existing addon
        if target_dir.exists():
            shutil.rmtree(target_dir)
            print("🗑️  Removed old addon")
        
        # Copy new version
        shutil.copytree(source_dir, target_dir)
        print("✅ Addon updated successfully!")
        
        print("\n🚀 Next steps:")
        print("1. In Blender, press F3 and search 'Reload Scripts'")
        print("2. Or restart Blender")
        print("3. Your changes are now active!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating addon: {e}")
        return False

def create_blender_reload_script():
    """Create a script you can run in Blender's text editor."""
    
    reload_script = '''
import bpy
import importlib
import sys

# Reload the linkage animator addon
addon_name = "linkage_animator"

# Unregister the addon
if addon_name in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_disable(module=addon_name)

# Reload all modules
for module_name in list(sys.modules.keys()):
    if module_name.startswith(addon_name):
        importlib.reload(sys.modules[module_name])

# Re-register the addon
bpy.ops.preferences.addon_enable(module=addon_name)

print("Linkage Animator addon reloaded!")
'''
    
    with open("blender_reload_script.py", "w", encoding='utf-8') as f:
        f.write(reload_script)
    
    print("📝 Created blender_reload_script.py")
    print("   Copy this script into Blender's Text Editor and run it to reload the addon")

if __name__ == "__main__":
    print("🔧 Blender Addon Development Helper")
    print("=" * 40)
    
    if not Path("linkage_animator").exists():
        print("❌ linkage_animator folder not found!")
        print("   Make sure you're running this from your project directory")
        sys.exit(1)
    
    # Update the addon
    success = update_blender_addon()
    
    # Create reload script
    create_blender_reload_script()
    
    if success:
        print("\n🎉 Development setup complete!")
        print("\n💡 Development Workflow:")
        print("1. Make changes to your addon code")
        print("2. Run: python update_blender_addon.py")
        print("3. In Blender: F3 → 'Reload Scripts'")
        print("4. Test your changes immediately!")
    else:
        print("\n❌ Setup failed. Check the error messages above.") 