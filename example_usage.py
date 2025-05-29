#!/usr/bin/env python3
"""
Robot Animator Plus Delux 3000 - Example Usage

This script demonstrates the key features of the robot animation system,
including natural language processing, motion planning, safety monitoring,
and Blender integration.
"""

import time
import json
import logging
from robot_animator import DataFlowPipeline, KeyframeProcessor, BlenderSceneManager, MotionPlanner, CobotSafetyMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main demonstration of the Robot Animator Plus Delux 3000 system."""
    
    print("🤖 Robot Animator Plus Delux 3000 - Example Usage")
    print("=" * 60)
    
    # Example 1: Basic Command Processing
    print("\n1️⃣ Basic Command Processing")
    print("-" * 30)
    
    # Initialize the pipeline
    pipeline = DataFlowPipeline()
    
    # Process a simple command
    command = "Pick up the red cube and place it on the table"
    print(f"Command: '{command}'")
    
    result = pipeline.process_command(command)
    
    if result["success"]:
        print("✅ Command processed successfully!")
        print(f"   Processing time: {result['processing_time']:.3f}s")
        print(f"   Estimated execution: {result['estimated_execution_time']:.2f}s")
        print(f"   Generated {len(result['keyframes']['keyframes'])} keyframes")
        print(f"   Safety checks: {result['safety_checks']['workspace_check']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Example 2: Advanced Configuration
    print("\n2️⃣ Advanced Configuration")
    print("-" * 30)
    
    # Custom configuration for industrial environment
    config = {
        "safety_enabled": True,
        "blender_visualization": True,
        "real_time_feedback": True,
        "trajectory_optimization": True,
        "collision_checking": True,
        "max_execution_time": 15.0,
        "frame_rate": 30,
        "joint_velocity_limit": 0.8,
        "workspace_bounds": {
            "x": (-0.8, 0.8),
            "y": (-0.6, 0.6),
            "z": (0.1, 1.2)
        }
    }
    
    industrial_pipeline = DataFlowPipeline(config)
    
    # Process command with context
    context = {
        "current_joint_angles": [0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
        "obstacles": [
            {"position": (0.3, 0.3, 0.5), "radius": 0.08},
            {"position": (-0.2, 0.4, 0.3), "radius": 0.05}
        ],
        "reference_position": (0.0, 0.4, 0.6)
    }
    
    command = "Move the robot arm to the left side carefully"
    print(f"Command: '{command}'")
    print(f"Context: {len(context['obstacles'])} obstacles detected")
    
    result = industrial_pipeline.process_command(command, context)
    
    if result["success"]:
        print("✅ Industrial command processed!")
        print(f"   Motion plan: {result['motion_plan']['action']}")
        print(f"   Target position: {result['motion_plan']['target_position']}")
        print(f"   Trajectory points: {result['motion_plan']['waypoint_count']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Example 3: Individual Component Testing
    print("\n3️⃣ Individual Component Testing")
    print("-" * 30)
    
    # Test keyframe processor
    print("Testing Keyframe Processor...")
    processor = KeyframeProcessor()
    
    sample_keyframes = {
        "armature": "TestRobot",
        "keyframes": [
            {"bone": "base_joint", "frame": 1, "rotation": (0, 0, 0), "interpolation": "BEZIER"},
            {"bone": "base_joint", "frame": 30, "rotation": (0, 0, 1.57), "interpolation": "BEZIER"}
        ]
    }
    
    if processor.validate_keyframe_data(sample_keyframes):
        print("✅ Keyframe validation passed")
        
        # Test interpolation
        start_rot = (0, 0, 0)
        end_rot = (0, 0, 1.57)
        interpolated = processor.interpolate_rotation(start_rot, end_rot, 0.5, "BEZIER")
        print(f"   Interpolated rotation: {interpolated}")
    else:
        print("❌ Keyframe validation failed")
    
    # Test motion planner
    print("\nTesting Motion Planner...")
    planner = MotionPlanner()
    
    # Parse natural language
    parsed = planner.parse_natural_language("Pick up the blue sphere quickly")
    print(f"✅ Parsed command: {parsed['action']} {parsed['target']['color']} {parsed['target']['type']}")
    
    # Test inverse kinematics
    target_pos = (0.5, 0.3, 0.8)
    joint_angles = planner.solve_inverse_kinematics(target_pos)
    print(f"✅ IK solution for {target_pos}: {[f'{a:.2f}' for a in joint_angles]}")
    
    # Test safety monitor
    print("\nTesting Safety Monitor...")
    safety_monitor = CobotSafetyMonitor()
    
    # Mock human detection
    safety_monitor._set_mock_human_count(1)
    import numpy as np
    mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    humans = safety_monitor.detect_humans(mock_frame)
    print(f"✅ Detected {len(humans)} humans")
    
    if humans:
        robot_pos = (0.0, 0.0, 0.0)
        violation = safety_monitor.check_safety_zone(humans[0]["position"], robot_pos)
        print(f"   Safety violation: {violation}")
    
    # Example 4: Real-time Feedback Simulation
    print("\n4️⃣ Real-time Feedback Simulation")
    print("-" * 30)
    
    # Setup mock sensor data callback
    def mock_sensor_callback():
        return {
            "camera": np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            "force_sensor": [0.5, 0.2, 0.1, 0.0, 0.0, 0.0],
            "joint_positions": [0.1, -1.5, 0.2, -1.6, 0.1, 0.0],
            "robot_position": (0.1, 0.2, 0.3),
            "timestamp": time.time()
        }
    
    # Start real-time feedback
    pipeline.start_real_time_feedback(mock_sensor_callback)
    print("✅ Real-time feedback started")
    
    # Simulate some processing time
    time.sleep(2.0)
    
    # Process sensor feedback manually
    sensor_data = mock_sensor_callback()
    feedback = pipeline.process_sensor_feedback(sensor_data)
    print(f"   Feedback status: {feedback['safety_status']}")
    print(f"   Adjustments needed: {len(feedback['adjustments'])}")
    
    # Stop feedback
    pipeline.stop_real_time_feedback()
    print("✅ Real-time feedback stopped")
    
    # Example 5: Multiple Command Sequence
    print("\n5️⃣ Multiple Command Sequence")
    print("-" * 30)
    
    commands = [
        "Move to the home position",
        "Pick up the red cube from the table",
        "Move above the blue box",
        "Place the cube in the box",
        "Return to home position"
    ]
    
    total_time = 0.0
    for i, cmd in enumerate(commands, 1):
        print(f"Step {i}: '{cmd}'")
        result = pipeline.process_command(cmd)
        
        if result["success"]:
            exec_time = result["estimated_execution_time"]
            total_time += exec_time
            print(f"   ✅ Planned ({exec_time:.1f}s)")
        else:
            print(f"   ❌ Failed: {result['error']}")
    
    print(f"\nTotal sequence time: {total_time:.1f}s")
    
    # Example 6: Safety Scenario Testing
    print("\n6️⃣ Safety Scenario Testing")
    print("-" * 30)
    
    # Test workspace boundary violation
    out_of_bounds_command = "Move to position 2.0, 2.0, 2.0"
    print(f"Testing: '{out_of_bounds_command}'")
    
    result = pipeline.process_command(out_of_bounds_command)
    if not result["success"]:
        print("✅ Safety system correctly rejected out-of-bounds command")
        print(f"   Issues: {result.get('safety_issues', [])}")
    else:
        print("❌ Safety system should have rejected this command")
    
    # Test emergency stop scenario
    print("\nTesting emergency stop...")
    safety_monitor.trigger_emergency_stop()
    
    if safety_monitor.emergency_stop_active:
        print("✅ Emergency stop activated")
        safety_monitor.reset_emergency_stop()
        print("✅ Emergency stop reset")
    
    # Example 7: Export and Logging
    print("\n7️⃣ Export and Logging")
    print("-" * 30)
    
    # Export keyframes to Blender script
    if result.get("keyframes"):
        blender_script = processor.export_to_blender_format(result["keyframes"])
        with open("robot_animation.py", "w") as f:
            f.write(blender_script)
        print("✅ Blender script exported to 'robot_animation.py'")
    
    # Export execution log
    pipeline.export_execution_log("execution_log.json")
    print("✅ Execution log exported to 'execution_log.json'")
    
    # Export safety log
    safety_monitor.export_safety_log("safety_log.json")
    print("✅ Safety log exported to 'safety_log.json'")
    
    # Example 8: System Status and Monitoring
    print("\n8️⃣ System Status and Monitoring")
    print("-" * 30)
    
    # Get pipeline status
    status = pipeline.get_pipeline_status()
    print("Pipeline Status:")
    print(f"   Execution status: {status['execution_status']}")
    print(f"   Real-time feedback: {status['real_time_feedback_active']}")
    print(f"   Safety monitoring: {status['safety_monitor_status']['monitoring_active']}")
    
    # Get safety status
    safety_status = safety_monitor.get_safety_status()
    print("\nSafety Status:")
    print(f"   Emergency stop: {safety_status['emergency_stop_active']}")
    print(f"   Detected humans: {safety_status['detected_humans']}")
    print(f"   Recent violations: {safety_status['recent_violations']}")
    
    # Example 9: Performance Benchmarking
    print("\n9️⃣ Performance Benchmarking")
    print("-" * 30)
    
    # Benchmark command processing
    test_commands = [
        "Pick up the object",
        "Move to the table",
        "Place the item carefully",
        "Return to home position"
    ]
    
    processing_times = []
    
    for cmd in test_commands:
        start_time = time.time()
        result = pipeline.process_command(cmd)
        end_time = time.time()
        
        processing_time = end_time - start_time
        processing_times.append(processing_time)
        
        print(f"'{cmd}': {processing_time:.3f}s")
    
    avg_time = sum(processing_times) / len(processing_times)
    print(f"\nAverage processing time: {avg_time:.3f}s")
    print(f"Commands per second: {1/avg_time:.1f}")
    
    # Final Summary
    print("\n🎉 Example Usage Complete!")
    print("=" * 60)
    print("Key achievements:")
    print("✅ Natural language command processing")
    print("✅ AI motion planning and trajectory generation")
    print("✅ Safety validation and monitoring")
    print("✅ Blender integration and keyframe generation")
    print("✅ Real-time feedback processing")
    print("✅ Multi-command sequence execution")
    print("✅ Safety scenario testing")
    print("✅ Export and logging capabilities")
    print("✅ Performance benchmarking")
    
    print(f"\nSystem ready for robot control integration!")
    print("Check the generated files:")
    print("- robot_animation.py (Blender script)")
    print("- execution_log.json (Pipeline log)")
    print("- safety_log.json (Safety events)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during example execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nExample execution finished.") 