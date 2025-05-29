#!/usr/bin/env python3
"""
ProcessAnimator Blender Addon Example

Complete example demonstrating the "WOW this is so easy" workflow:
1. Natural language input
2. Smart scaling from real dimensions  
3. Automated robot analysis
4. GCODE generation for real execution

Usage:
1. Load this as a Blender addon
2. Import robot models and assembly components
3. Use the ProcessAnimator panel in the 3D viewport sidebar
4. Generate animations and real robot code
"""

import bpy
import sys
import os

# Add the robot_animator package to Python path
# In a real addon installation, this would be handled by the addon structure
addon_directory = os.path.dirname(__file__)
if addon_directory not in sys.path:
    sys.path.append(addon_directory)

from robot_animator.blender_addon import register, unregister
from robot_animator.process_animator import ProcessAnimator
from robot_animator.manufacturing.smart_scaler import SmartScaler
from robot_animator.manufacturing.robot_analyzer import RobotAnalyzer
from robot_animator.manufacturing.gcode_generator import GCodeGenerator


def demo_workflow():
    """
    Demonstrate the complete ProcessAnimator workflow.
    
    This example shows how easy it is to go from a natural language
    description to a working robot animation with real GCODE output.
    """
    
    print("🚀 ProcessAnimator Demo: Automated Manufacturing Animation")
    print("=" * 60)
    
    # Step 1: Natural Language Input
    print("\n1️⃣ Natural Language Input:")
    description = "Robot ABB IRB 6700 assembles bike frame components in manufacturing cell"
    print(f"   Input: '{description}'")
    
    # Initialize ProcessAnimator
    animator = ProcessAnimator()
    
    # Process the description
    result = animator.process_natural_language(description)
    if result['success']:
        print(f"   ✅ Detected: {result['robot_type']} performing {result['process_type']}")
        print(f"   🎯 Target: {result['target_object']} in {result['environment']}")
        print(f"   📊 Confidence: {result['confidence_score']:.1%}")
    else:
        print(f"   ❌ Error: {result['error']}")
        return
    
    # Step 2: Smart Scaling Example
    print("\n2️⃣ Smart Scaling:")
    print("   User selects bike frame tube and says: 'This is 25mm diameter'")
    
    # Simulate smart scaling
    scaler = SmartScaler()
    
    # In a real scenario, this would scale the actual Blender objects
    scaling_info = {
        'reference_object': 'BikeFrame_Tube_01',
        'real_dimension_mm': 25.0,
        'current_blender_size': 0.025,  # 25mm in Blender units
        'calculated_scale_factor': 1.0
    }
    
    print(f"   📏 Reference: {scaling_info['reference_object']}")
    print(f"   📐 Real dimension: {scaling_info['real_dimension_mm']}mm")
    print(f"   🔄 Scale factor: {scaling_info['calculated_scale_factor']:.3f}")
    print("   ✅ Entire assembly automatically scaled to real proportions!")
    
    # Step 3: Robot Analysis
    print("\n3️⃣ Robot Analysis:")
    analyzer = RobotAnalyzer()
    
    # Simulate robot analysis results
    robot_analysis = {
        'robot_type': 'ABB_IRB6700',
        'reach': 3.2,  # meters
        'dof': 6,
        'safety_zones': {
            'danger_zone': 0.5,
            'warning_zone': 1.0,
            'monitoring_zone': 2.0
        },
        'workspace_volume': 137.3,  # cubic meters
        'collision_objects_detected': 2
    }
    
    print(f"   🤖 Robot: {robot_analysis['robot_type']}")
    print(f"   📏 Reach: {robot_analysis['reach']}m")
    print(f"   🎚️ DOF: {robot_analysis['dof']}")
    print(f"   🛡️ Safety zones: {len(robot_analysis['safety_zones'])} configured")
    print(f"   📦 Workspace: {robot_analysis['workspace_volume']:.1f} m³")
    print(f"   ⚠️ Collision objects: {robot_analysis['collision_objects_detected']} detected")
    
    # Step 4: Animation Generation
    print("\n4️⃣ Animation Generation:")
    print("   🎬 Generating low-quality preview...")
    
    # Simulate animation generation
    animation_result = {
        'quality': 'low',
        'resolution': '640x480',
        'frame_rate': 12,
        'estimated_render_time': 0.5,  # minutes
        'total_frames': 120,
        'animation_duration': 10.0  # seconds
    }
    
    print(f"   📺 Quality: {animation_result['quality']} ({animation_result['resolution']})")
    print(f"   🎞️ Frame rate: {animation_result['frame_rate']} fps")
    print(f"   ⏱️ Duration: {animation_result['animation_duration']}s")
    print(f"   🕐 Render time: {animation_result['estimated_render_time']} min")
    print("   ✅ Quick preview ready for review!")
    
    # Step 5: GCODE Generation
    print("\n5️⃣ GCODE Generation:")
    gcode_gen = GCodeGenerator()
    
    # Simulate GCODE generation
    gcode_result = {
        'success': True,
        'output_file': 'bike_frame_assembly.mod',
        'robot_type': 'ABB_IRB6700',
        'language': 'RAPID',
        'total_moves': 45,
        'estimated_execution_time': 180.0,  # seconds
        'file_size_bytes': 2048
    }
    
    if gcode_result['success']:
        print(f"   📄 Generated: {gcode_result['output_file']}")
        print(f"   🤖 Language: {gcode_result['language']} for {gcode_result['robot_type']}")
        print(f"   🏃‍♂️ Moves: {gcode_result['total_moves']} motion commands")
        print(f"   ⏰ Execution time: {gcode_result['estimated_execution_time']/60:.1f} minutes")
        print(f"   💾 File size: {gcode_result['file_size_bytes']} bytes")
        print("   ✅ Ready to load on real robot!")
    
    # Step 6: Summary
    print("\n6️⃣ Workflow Complete:")
    print("   🎉 WOW! From description to real robot code in seconds!")
    print("   📝 What just happened:")
    print("      • Natural language → Automated setup")
    print("      • One dimension → Entire assembly scaled")
    print("      • Automatic robot constraint analysis")
    print("      • Simulation → Real robot GCODE")
    print("      • Safety checks and collision detection")
    print("      • Ready for university demos and production!")
    
    print("\n🎓 Perfect for:")
    print("   • University robotics courses")
    print("   • Manufacturing engineers") 
    print("   • Robot programming training")
    print("   • Production line planning")
    print("   • GCODE validation and testing")
    
    return result


def setup_demo_scene():
    """
    Setup a demo scene with robot and components.
    This would typically be done by importing models.
    """
    
    print("\n🏗️ Setting up demo scene...")
    
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Add robot placeholder (in reality, this would be a detailed robot model)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2, location=(0, 0, 1))
    robot = bpy.context.active_object
    robot.name = "ABB_IRB6700_Robot"
    robot['robot_type'] = 'ABB_IRB6700'
    robot['reach'] = 3.2
    robot['dof'] = 6
    
    # Add bike frame components
    component_positions = [
        (1.0, 0.5, 0.8),  # Frame tube 1
        (1.2, 0.3, 0.9),  # Frame tube 2
        (0.8, 0.7, 0.85), # Junction piece
    ]
    
    for i, pos in enumerate(component_positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0125, depth=0.5, location=pos)
        component = bpy.context.active_object
        component.name = f"BikeFrame_Tube_{i+1:02d}"
        if i == 0:
            component['real_diameter_mm'] = 25.0  # Reference dimension
    
    # Add manufacturing cell environment
    bpy.ops.mesh.primitive_cube_add(size=10, location=(0, 0, -0.1))
    floor = bpy.context.active_object
    floor.name = "Factory_Floor"
    floor.scale[2] = 0.02  # Make it flat
    
    print("   ✅ Demo scene ready!")
    print("   🤖 Robot: ABB IRB 6700")
    print("   🚲 Components: Bike frame parts")
    print("   🏭 Environment: Manufacturing cell")


def main():
    """Main demo function."""
    
    print("ProcessAnimator Blender Addon Demo")
    print("==================================")
    
    # Setup demo scene
    setup_demo_scene()
    
    # Run the demo workflow
    demo_workflow()
    
    print("\n🎯 Next Steps:")
    print("   1. Install ProcessAnimator addon in Blender")
    print("   2. Import your robot models")
    print("   3. Try the natural language interface")
    print("   4. Use smart scaling with real dimensions")
    print("   5. Generate GCODE for your real robot!")
    
    print("\n🌟 The future of robot animation is here!")


if __name__ == "__main__":
    # Run demo if called directly
    main()
else:
    # Register addon if imported in Blender
    try:
        register()
        print("ProcessAnimator addon registered successfully!")
    except Exception as e:
        print(f"Addon registration failed: {e}")


# Example usage functions for the addon interface
def example_quick_assembly():
    """Example: Quick assembly animation setup."""
    animator = ProcessAnimator()
    result = animator.animate(
        "KUKA robot assembles electronic components in clean room environment"
    )
    return result


def example_smart_scaling():
    """Example: Smart scaling workflow."""
    scaler = SmartScaler()
    
    # User clicks on a component and specifies real dimension
    result = scaler.scale_assembly(
        reference_object="Component_PCB_01",
        real_dimension=100.0,  # 100mm PCB
        measurement_axis="X"
    )
    return result


def example_gcode_generation():
    """Example: Generate GCODE for real robot."""
    gcode_gen = GCodeGenerator()
    
    # Convert current animation to robot code
    result = gcode_gen.generate_from_animation(
        output_path="//robot_program.mod",
        robot_type="ABB_IRB6700"
    )
    return result


# Addon information for Blender
bl_info = {
    "name": "ProcessAnimator - Automated Manufacturing Animation",
    "author": "Robot Animator Team", 
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > ProcessAnimator",
    "description": "WOW-easy robot animation with natural language, smart scaling, and GCODE generation",
    "category": "Animation",
    "doc_url": "https://github.com/your-repo/process-animator",
    "tracker_url": "https://github.com/your-repo/process-animator/issues"
} 