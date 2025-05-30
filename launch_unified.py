import subprocess
import sys
import os

def launch_unified_robot_nlp():
    """Launch Blender with unified Robot NLP addon."""
    
    # Blender detection paths
    blender_paths = [
        r'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 4.1\blender.exe', 
        r'C:\Program Files\Blender Foundation\Blender 4.0\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 3.6\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 3.5\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 3.4\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 3.3\blender.exe',
        r'C:\Program Files\Blender Foundation\Blender 3.2\blender.exe',
        'blender'  # Try system PATH
    ]

    blender_path = None
    for path in blender_paths:
        if os.path.exists(path):
            blender_path = path
            print(f'✅ Found Blender: {path}')
            break

    if not blender_path:
        try:
            subprocess.run(['blender', '--version'], capture_output=True, timeout=5)
            blender_path = 'blender'
            print('✅ Using Blender from system PATH')
        except:
            print('❌ Blender not found! Please install Blender 3.2+')
            input('Press Enter to exit...')
            sys.exit(1)

    # Launch with unified addon
    addon_path = os.path.abspath('robot_nlp_unified.py')
    print(f'🚀 Loading unified addon: {addon_path}')
    print('🎯 Look for "Robot NLP" tab in 3D viewport sidebar (press N if hidden)')
    print('🎨 Use the dropdown to select your preferred interface style!')
    
    # Launch Blender
    try:
        subprocess.run([blender_path, '--python', addon_path])
        print('✅ Blender session completed successfully')
    except Exception as e:
        print(f'❌ Error launching Blender: {e}')
        input('Press Enter to exit...')

if __name__ == "__main__":
    launch_unified_robot_nlp() 