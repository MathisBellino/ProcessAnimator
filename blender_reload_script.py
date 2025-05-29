
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
