#!/usr/bin/env python3
"""
Test Suite for Multi-Bar Linkage Animator

Tests all core functionality:
- Linkage mechanism creation
- Constraint solving
- Automatic Blender setup
- Animation generation
"""

import unittest
import math
from typing import Dict, Any, List, Tuple, Optional
import sys
import os

# Add the addon path for testing
sys.path.append(os.path.dirname(__file__))

try:
    # Try to import Blender modules for full testing
    import bpy
    import bmesh
    import mathutils
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: Blender modules not available. Running standalone tests only.")


class TestLinkageMechanisms(unittest.TestCase):
    """Test linkage mechanism definitions and kinematics."""
    
    def setUp(self):
        """Set up test fixtures."""
        if BLENDER_AVAILABLE:
            # Clear scene
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
    
    def test_four_bar_linkage_creation(self):
        """Test creating a four-bar linkage mechanism."""
        from linkage_animator.core.linkage_mechanisms import FourBarLinkage
        
        # Define four-bar linkage parameters
        ground_link_length = 10.0
        input_link_length = 3.0
        coupler_link_length = 8.0
        output_link_length = 5.0
        
        linkage = FourBarLinkage(
            ground_length=ground_link_length,
            input_length=input_link_length,
            coupler_length=coupler_link_length,
            output_length=output_link_length
        )
        
        # Test basic properties
        self.assertEqual(linkage.ground_length, ground_link_length)
        self.assertEqual(linkage.input_length, input_link_length)
        self.assertEqual(linkage.coupler_length, coupler_link_length)
        self.assertEqual(linkage.output_length, output_link_length)
        
        # Test Grashof condition
        grashof_result = linkage.check_grashof_condition()
        self.assertIsInstance(grashof_result, dict)
        self.assertIn('type', grashof_result)
        self.assertIn('is_grashof', grashof_result)
        
    def test_four_bar_position_analysis(self):
        """Test four-bar linkage position analysis."""
        from linkage_animator.core.linkage_mechanisms import FourBarLinkage
        
        linkage = FourBarLinkage(10.0, 3.0, 8.0, 5.0)
        
        # Test position analysis at various input angles
        test_angles = [0, 30, 60, 90, 120, 180, 270]
        
        for input_angle in test_angles:
            input_rad = math.radians(input_angle)
            positions = linkage.solve_positions(input_rad)
            
            self.assertIsInstance(positions, dict)
            self.assertIn('coupler_angle', positions)
            self.assertIn('output_angle', positions)
            self.assertIn('joint_positions', positions)
            
            # Verify joint positions are valid
            joint_positions = positions['joint_positions']
            self.assertEqual(len(joint_positions), 4)  # 4 joints in four-bar
            
            # Check that distances are maintained
            ground_joint = Vector(joint_positions[0])
            input_joint = Vector(joint_positions[1])
            coupler_joint = Vector(joint_positions[2])
            output_joint = Vector(joint_positions[3])
            
            # Verify link lengths
            input_length_calc = (input_joint - ground_joint).length
            self.assertAlmostEqual(input_length_calc, linkage.input_length, places=3)
            
            coupler_length_calc = (coupler_joint - input_joint).length
            self.assertAlmostEqual(coupler_length_calc, linkage.coupler_length, places=3)
    
    def test_slider_crank_mechanism(self):
        """Test slider-crank mechanism."""
        from linkage_animator.core.linkage_mechanisms import SliderCrankMechanism
        
        crank_length = 2.0
        connecting_rod_length = 6.0
        
        mechanism = SliderCrankMechanism(crank_length, connecting_rod_length)
        
        # Test various crank angles
        for angle in range(0, 360, 30):
            angle_rad = math.radians(angle)
            positions = mechanism.solve_positions(angle_rad)
            
            self.assertIn('slider_position', positions)
            self.assertIn('connecting_rod_angle', positions)
            self.assertIn('joint_positions', positions)
            
            # Verify connecting rod length is maintained
            joint_positions = positions['joint_positions']
            crank_pin = Vector(joint_positions[1])
            slider = Vector(joint_positions[2])
            
            rod_length_calc = (slider - crank_pin).length
            self.assertAlmostEqual(rod_length_calc, connecting_rod_length, places=3)


class TestConstraintSolver(unittest.TestCase):
    """Test constraint-based animation solver."""
    
    def test_distance_constraint(self):
        """Test distance constraint enforcement."""
        from linkage_animator.core.constraint_solver import ConstraintSolver
        
        solver = ConstraintSolver()
        
        # Create two points with a distance constraint
        point_a = Vector((0, 0, 0))
        point_b = Vector((3, 4, 0))
        target_distance = 5.0
        
        constraint = {
            'type': 'distance',
            'points': [point_a, point_b],
            'target_distance': target_distance
        }
        
        # Solve constraint
        result = solver.solve_constraint(constraint)
        
        self.assertTrue(result['solved'])
        self.assertAlmostEqual(result['error'], 0.0, places=3)
        
        # Verify distance is correct
        solved_distance = (result['points'][1] - result['points'][0]).length
        self.assertAlmostEqual(solved_distance, target_distance, places=3)
    
    def test_angle_constraint(self):
        """Test angle constraint enforcement."""
        from linkage_animator.core.constraint_solver import ConstraintSolver
        
        solver = ConstraintSolver()
        
        # Create three points forming an angle
        point_a = Vector((1, 0, 0))
        point_b = Vector((0, 0, 0))  # Vertex
        point_c = Vector((0, 1, 0))
        target_angle = math.radians(90)  # 90 degrees
        
        constraint = {
            'type': 'angle',
            'points': [point_a, point_b, point_c],
            'target_angle': target_angle
        }
        
        result = solver.solve_constraint(constraint)
        self.assertTrue(result['solved'])
    
    def test_multi_constraint_system(self):
        """Test solving multiple constraints simultaneously."""
        from linkage_animator.core.constraint_solver import ConstraintSolver
        
        solver = ConstraintSolver()
        
        # Create a simple triangle with fixed side lengths
        constraints = [
            {
                'type': 'distance',
                'points': [Vector((0, 0, 0)), Vector((3, 0, 0))],
                'target_distance': 3.0
            },
            {
                'type': 'distance',
                'points': [Vector((3, 0, 0)), Vector((0, 4, 0))],
                'target_distance': 5.0
            },
            {
                'type': 'distance',
                'points': [Vector((0, 4, 0)), Vector((0, 0, 0))],
                'target_distance': 4.0
            }
        ]
        
        result = solver.solve_constraints(constraints)
        self.assertTrue(result['converged'])
        self.assertLess(result['total_error'], 0.01)


class TestBlenderIntegration(unittest.TestCase):
    """Test automatic Blender setup and integration."""
    
    def setUp(self):
        """Set up Blender scene for testing."""
        if not BLENDER_AVAILABLE:
            self.skipTest("Blender not available")
        
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    
    def test_automatic_armature_creation(self):
        """Test automatic creation of armatures for linkages."""
        from linkage_animator.blender.auto_setup import BlenderAutoSetup
        
        setup = BlenderAutoSetup()
        
        # Create a four-bar linkage armature
        linkage_config = {
            'type': 'four_bar',
            'ground_length': 10.0,
            'input_length': 3.0,
            'coupler_length': 8.0,
            'output_length': 5.0,
            'name': 'TestFourBar'
        }
        
        result = setup.create_linkage_armature(linkage_config)
        
        self.assertTrue(result['success'])
        self.assertIn('armature_object', result)
        
        # Verify armature was created
        armature_obj = result['armature_object']
        self.assertEqual(armature_obj.type, 'ARMATURE')
        self.assertGreaterEqual(len(armature_obj.data.bones), 4)
        
        # Verify constraints were applied
        pose_bones = armature_obj.pose.bones
        constraint_count = sum(len(bone.constraints) for bone in pose_bones)
        self.assertGreater(constraint_count, 0)
    
    def test_constraint_setup(self):
        """Test automatic constraint setup for linkages."""
        from linkage_animator.blender.auto_setup import BlenderAutoSetup
        
        setup = BlenderAutoSetup()
        
        # Create linkage first
        linkage_config = {
            'type': 'slider_crank',
            'crank_length': 2.0,
            'connecting_rod_length': 6.0,
            'name': 'TestSliderCrank'
        }
        
        result = setup.create_linkage_armature(linkage_config)
        armature_obj = result['armature_object']
        
        # Verify IK constraints for maintaining link lengths
        pose_bones = armature_obj.pose.bones
        ik_constraints = []
        
        for bone in pose_bones:
            for constraint in bone.constraints:
                if constraint.type == 'IK':
                    ik_constraints.append(constraint)
        
        self.assertGreater(len(ik_constraints), 0)
    
    def test_animation_keyframe_generation(self):
        """Test automatic keyframe generation for linkage animation."""
        from linkage_animator.animation.keyframe_generator import KeyframeGenerator
        
        generator = KeyframeGenerator()
        
        # Create a simple rotation animation for a four-bar linkage
        animation_config = {
            'linkage_type': 'four_bar',
            'input_motion': {
                'type': 'rotation',
                'start_angle': 0,
                'end_angle': 360,
                'duration': 120  # frames
            },
            'frame_rate': 24
        }
        
        keyframes = generator.generate_linkage_animation(animation_config)
        
        self.assertIsInstance(keyframes, list)
        self.assertGreater(len(keyframes), 0)
        
        # Verify keyframe structure
        for keyframe in keyframes[:5]:  # Check first 5 keyframes
            self.assertIn('frame', keyframe)
            self.assertIn('bone_name', keyframe)
            self.assertIn('rotation', keyframe)


class TestAnimationGeneration(unittest.TestCase):
    """Test complete animation generation pipeline."""
    
    def test_four_bar_complete_animation(self):
        """Test complete four-bar linkage animation generation."""
        if not BLENDER_AVAILABLE:
            self.skipTest("Blender not available")
        
        from linkage_animator.animation.linkage_animator import LinkageAnimator
        
        animator = LinkageAnimator()
        
        animation_request = {
            'linkage_type': 'four_bar',
            'parameters': {
                'ground_length': 10.0,
                'input_length': 3.0,
                'coupler_length': 8.0,
                'output_length': 5.0
            },
            'motion': {
                'type': 'constant_rotation',
                'rpm': 60,
                'duration': 5.0  # seconds
            },
            'visualization': {
                'show_constraints': True,
                'show_motion_path': True,
                'quality': 'medium'
            }
        }
        
        result = animator.create_animation(animation_request)
        
        self.assertTrue(result['success'])
        self.assertIn('armature_object', result)
        self.assertIn('animation_data', result)
        self.assertGreater(result['frame_count'], 0)
    
    def test_slider_crank_animation(self):
        """Test slider-crank mechanism animation."""
        if not BLENDER_AVAILABLE:
            self.skipTest("Blender not available")
        
        from linkage_animator.animation.linkage_animator import LinkageAnimator
        
        animator = LinkageAnimator()
        
        animation_request = {
            'linkage_type': 'slider_crank',
            'parameters': {
                'crank_length': 2.0,
                'connecting_rod_length': 6.0
            },
            'motion': {
                'type': 'constant_rotation',
                'rpm': 120,
                'duration': 3.0
            }
        }
        
        result = animator.create_animation(animation_request)
        
        self.assertTrue(result['success'])
        
        # Verify slider motion constraints
        armature_obj = result['armature_object']
        slider_bone = None
        
        for bone in armature_obj.pose.bones:
            if 'slider' in bone.name.lower():
                slider_bone = bone
                break
        
        self.assertIsNotNone(slider_bone)
        
        # Check for location constraints on slider
        location_constraints = [c for c in slider_bone.constraints if c.type == 'LIMIT_LOCATION']
        self.assertGreater(len(location_constraints), 0)


if __name__ == '__main__':
    print("Running Multi-Bar Linkage Animator Test Suite")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestLinkageMechanisms))
    suite.addTest(unittest.makeSuite(TestConstraintSolver))
    
    if BLENDER_AVAILABLE:
        suite.addTest(unittest.makeSuite(TestBlenderIntegration))
        suite.addTest(unittest.makeSuite(TestAnimationGeneration))
        print("Full test suite with Blender integration")
    else:
        print("Standalone test suite (Blender modules not available)")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        
    print(f"Tests run: {result.testsRun}")
    print("=" * 50) 