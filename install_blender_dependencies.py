#!/usr/bin/env python3
"""
Install NLP dependencies in Blender's Python environment
"""

import os
import sys
import subprocess

def main():
    print("🔧 Installing NLP Dependencies for Blender")
    print("="*50)
    
    # Find Blender's Python executable
    blender_python_paths = [
        r"C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\3.6\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.5\3.5\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.4\3.4\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.3\3.3\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.2\3.2\python\bin\python.exe",
    ]
    
    blender_python = None
    for path in blender_python_paths:
        if os.path.exists(path):
            blender_python = path
            print(f"✅ Found Blender Python: {path}")
            break
    
    # Try to find it dynamically
    if not blender_python:
        program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
        for pf in program_files:
            blender_foundation = os.path.join(pf, "Blender Foundation")
            if os.path.exists(blender_foundation):
                for blender_version in os.listdir(blender_foundation):
                    version_dir = os.path.join(blender_foundation, blender_version)
                    if os.path.isdir(version_dir):
                        # Look for python in version subdirectory
                        for subdir in os.listdir(version_dir):
                            python_path = os.path.join(version_dir, subdir, "python", "bin", "python.exe")
                            if os.path.exists(python_path):
                                blender_python = python_path
                                print(f"✅ Found Blender Python: {python_path}")
                                break
                        if blender_python:
                            break
                if blender_python:
                    break
    
    if not blender_python:
        print("❌ Could not find Blender's Python installation")
        print("Please install the dependencies manually in Blender:")
        print("1. Open Blender")
        print("2. Go to Scripting tab")
        print("3. Run this script:")
        print("""
import subprocess
import sys

subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sentence-transformers'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy'])
subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
""")
        input("Press Enter to continue...")
        return
    
    print("🚀 Installing packages...")
    
    try:
        # Install sentence-transformers
        print("📦 Installing sentence-transformers...")
        subprocess.run([blender_python, '-m', 'pip', 'install', 'sentence-transformers'], check=True)
        
        # Install spacy
        print("📦 Installing spacy...")
        subprocess.run([blender_python, '-m', 'pip', 'install', 'spacy'], check=True)
        
        # Download spacy model
        print("📦 Downloading spacy English model...")
        subprocess.run([blender_python, '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
        
        print("✅ All dependencies installed successfully!")
        print("🚀 You can now use the Robot NLP addon in Blender!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("You may need to run as administrator or install manually.")
    
    input("Press Enter to continue...")

if __name__ == "__main__":
    main() 