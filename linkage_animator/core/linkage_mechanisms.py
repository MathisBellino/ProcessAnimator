#!/usr/bin/env python3
"""
Linkage Mechanisms - Core kinematic definitions and solvers

Provides mathematical definitions and solution methods for:
- Four-bar linkages
- Slider-crank mechanisms  
- Six-bar linkages
- Other multi-bar mechanisms
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LinkageType(Enum):
    """Types of linkage mechanisms."""
    FOUR_BAR = "four_bar"
    SLIDER_CRANK = "slider_crank"
    SIX_BAR_WATT = "six_bar_watt"
    SIX_BAR_STEPHENSON = "six_bar_stephenson"
    SCOTCH_YOKE = "scotch_yoke"
    GENEVA_DRIVE = "geneva_drive"
    CAM_FOLLOWER = "cam_follower"


@dataclass
class LinkageJoint:
    """Definition of a linkage joint."""
    name: str
    position: Tuple[float, float, float]
    joint_type: str  # 'revolute', 'prismatic', 'fixed'
    axis: Tuple[float, float, float] = (0, 0, 1)  # Rotation/translation axis
    limits: Tuple[float, float] = (-math.pi, math.pi)  # Joint limits


@dataclass
class LinkageLink:
    """Definition of a linkage link."""
    name: str
    length: float
    start_joint: str
    end_joint: str
    mass: float = 1.0
    inertia: float = 1.0


class FourBarLinkage:
    """
    Four-bar linkage mechanism.
    
    Classic planar four-bar linkage with ground, input, coupler, and output links.
    Provides position analysis, velocity analysis, and motion characteristics.
    """
    
    def __init__(self, ground_length: float, input_length: float, 
                 coupler_length: float, output_length: float):
        """
        Initialize four-bar linkage.
        
        Args:
            ground_length: Length of ground link
            input_length: Length of input (crank) link  
            coupler_length: Length of coupler link
            output_length: Length of output (rocker) link
        """
        self.ground_length = ground_length
        self.input_length = input_length
        self.coupler_length = coupler_length
        self.output_length = output_length
        
        # Joint definitions
        self.joints = [
            LinkageJoint("ground_start", (0, 0, 0), "fixed"),
            LinkageJoint("input_joint", (0, 0, 0), "revolute"),
            LinkageJoint("coupler_joint", (0, 0, 0), "revolute"),
            LinkageJoint("ground_end", (ground_length, 0, 0), "fixed"),
        ]
        
        # Link definitions
        self.links = [
            LinkageLink("ground", ground_length, "ground_start", "ground_end"),
            LinkageLink("input", input_length, "ground_start", "input_joint"),
            LinkageLink("coupler", coupler_length, "input_joint", "coupler_joint"),
            LinkageLink("output", output_length, "coupler_joint", "ground_end"),
        ]
        
        logger.info(f"Four-bar linkage created: {ground_length}, {input_length}, {coupler_length}, {output_length}")
    
    def check_grashof_condition(self) -> Dict[str, Any]:
        """
        Check Grashof condition for the four-bar linkage.
        
        Returns:
            Dictionary with Grashof analysis results
        """
        lengths = [self.ground_length, self.input_length, self.coupler_length, self.output_length]
        lengths.sort()
        
        shortest = lengths[0]
        longest = lengths[3]
        other1 = lengths[1]
        other2 = lengths[2]
        
        # Grashof condition: s + l ≤ p + q
        grashof_sum = shortest + longest
        other_sum = other1 + other2
        
        is_grashof = grashof_sum <= other_sum
        
        # Determine linkage type
        if is_grashof:
            if shortest == self.ground_length:
                linkage_type = "Crank-Rocker"
                motion_type = "One complete rotation possible"
            elif shortest == self.input_length or shortest == self.output_length:
                linkage_type = "Double-Crank"
                motion_type = "Both cranks can rotate completely"
            else:
                linkage_type = "Double-Rocker"
                motion_type = "Both links oscillate"
        else:
            linkage_type = "Triple-Rocker"
            motion_type = "All links oscillate"
        
        return {
            'is_grashof': is_grashof,
            'type': linkage_type,
            'motion_type': motion_type,
            'grashof_sum': grashof_sum,
            'other_sum': other_sum
        }
    
    def solve_positions(self, input_angle: float) -> Dict[str, Any]:
        """
        Solve position analysis for given input angle.
        
        Args:
            input_angle: Input link angle in radians
            
        Returns:
            Dictionary with joint positions and link angles
        """
        try:
            # Ground link fixed positions
            A = np.array([0, 0])  # Ground start
            B = np.array([self.ground_length, 0])  # Ground end
            
            # Input link position
            C = A + self.input_length * np.array([math.cos(input_angle), math.sin(input_angle)])
            
            # Solve for output link angle using cosine rule
            # Vector from B to C
            BC = C - B
            BC_length = np.linalg.norm(BC)
            
            # Check if configuration is possible
            if BC_length > (self.coupler_length + self.output_length):
                raise ValueError("Links cannot reach - configuration impossible")
            if BC_length < abs(self.coupler_length - self.output_length):
                raise ValueError("Links overlap - configuration impossible")
            
            # Angle of BC vector
            gamma = math.atan2(BC[1], BC[0])
            
            # Use cosine rule to find angles
            cos_alpha = (self.output_length**2 + BC_length**2 - self.coupler_length**2) / (2 * self.output_length * BC_length)
            cos_alpha = max(-1, min(1, cos_alpha))  # Clamp to valid range
            
            alpha = math.acos(cos_alpha)
            
            # Two possible positions for output link
            output_angle_1 = gamma + alpha
            output_angle_2 = gamma - alpha
            
            # Choose the configuration (usually take the one that gives continuous motion)
            output_angle = output_angle_1
            
            # Calculate coupler angle
            D = B + self.output_length * np.array([math.cos(output_angle), math.sin(output_angle)])
            
            # Verify coupler link
            CD = D - C
            coupler_angle = math.atan2(CD[1], CD[0])
            
            # Joint positions
            joint_positions = [
                (A[0], A[1], 0),  # Ground start
                (C[0], C[1], 0),  # Input joint
                (D[0], D[1], 0),  # Coupler joint  
                (B[0], B[1], 0),  # Ground end
            ]
            
            return {
                'success': True,
                'input_angle': input_angle,
                'output_angle': output_angle,
                'coupler_angle': coupler_angle,
                'joint_positions': joint_positions,
                'link_angles': {
                    'input': input_angle,
                    'output': output_angle,
                    'coupler': coupler_angle
                }
            }
            
        except Exception as e:
            logger.error(f"Position analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'joint_positions': [(0, 0, 0)] * 4
            }
    
    def solve_velocities(self, input_angle: float, input_velocity: float) -> Dict[str, Any]:
        """
        Solve velocity analysis for the four-bar linkage.
        
        Args:
            input_angle: Input link angle in radians
            input_velocity: Input angular velocity in rad/s
            
        Returns:
            Dictionary with velocity analysis results
        """
        positions = self.solve_positions(input_angle)
        if not positions['success']:
            return positions
        
        # Use velocity analysis equations for four-bar linkage
        # This is a simplified version - full implementation would use complex analysis
        
        output_angle = positions['output_angle']
        coupler_angle = positions['coupler_angle']
        
        # Simplified velocity relationships
        # In practice, this would use proper kinematic analysis
        velocity_ratio = (self.input_length * math.sin(coupler_angle - input_angle)) / \
                        (self.output_length * math.sin(output_angle - coupler_angle))
        
        output_velocity = input_velocity * velocity_ratio
        
        return {
            'success': True,
            'input_velocity': input_velocity,
            'output_velocity': output_velocity,
            'velocity_ratio': velocity_ratio,
            'coupler_velocity': {
                'linear': input_velocity * self.input_length,
                'angular': input_velocity
            }
        }


class SliderCrankMechanism:
    """
    Slider-crank mechanism.
    
    Converts rotational motion to linear motion using a crank and connecting rod.
    """
    
    def __init__(self, crank_length: float, connecting_rod_length: float):
        """
        Initialize slider-crank mechanism.
        
        Args:
            crank_length: Length of the crank
            connecting_rod_length: Length of connecting rod
        """
        self.crank_length = crank_length
        self.connecting_rod_length = connecting_rod_length
        
        # Joint definitions
        self.joints = [
            LinkageJoint("crank_center", (0, 0, 0), "fixed"),
            LinkageJoint("crank_pin", (0, 0, 0), "revolute"),
            LinkageJoint("slider", (0, 0, 0), "prismatic", axis=(1, 0, 0)),
        ]
        
        # Link definitions
        self.links = [
            LinkageLink("crank", crank_length, "crank_center", "crank_pin"),
            LinkageLink("connecting_rod", connecting_rod_length, "crank_pin", "slider"),
        ]
        
        logger.info(f"Slider-crank mechanism created: crank={crank_length}, rod={connecting_rod_length}")
    
    def solve_positions(self, crank_angle: float) -> Dict[str, Any]:
        """
        Solve position analysis for given crank angle.
        
        Args:
            crank_angle: Crank angle in radians
            
        Returns:
            Dictionary with joint positions and slider position
        """
        try:
            # Crank center fixed at origin
            crank_center = np.array([0, 0])
            
            # Crank pin position
            crank_pin = crank_center + self.crank_length * np.array([math.cos(crank_angle), math.sin(crank_angle)])
            
            # Slider position (on X-axis)
            # Use geometry to find slider position
            x_slider = crank_pin[0] + math.sqrt(self.connecting_rod_length**2 - crank_pin[1]**2)
            slider_pos = np.array([x_slider, 0])
            
            # Connecting rod angle
            rod_vector = slider_pos - crank_pin
            connecting_rod_angle = math.atan2(rod_vector[1], rod_vector[0])
            
            # Joint positions
            joint_positions = [
                (crank_center[0], crank_center[1], 0),  # Crank center
                (crank_pin[0], crank_pin[1], 0),       # Crank pin
                (slider_pos[0], slider_pos[1], 0),     # Slider
            ]
            
            return {
                'success': True,
                'crank_angle': crank_angle,
                'slider_position': x_slider,
                'connecting_rod_angle': connecting_rod_angle,
                'joint_positions': joint_positions,
                'crank_pin_position': (crank_pin[0], crank_pin[1]),
                'slider_displacement': x_slider - self.crank_length
            }
            
        except Exception as e:
            logger.error(f"Slider-crank position analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'joint_positions': [(0, 0, 0)] * 3
            }
    
    def solve_velocities(self, crank_angle: float, crank_velocity: float) -> Dict[str, Any]:
        """
        Solve velocity analysis for slider-crank.
        
        Args:
            crank_angle: Crank angle in radians
            crank_velocity: Crank angular velocity in rad/s
            
        Returns:
            Dictionary with velocity analysis results
        """
        positions = self.solve_positions(crank_angle)
        if not positions['success']:
            return positions
        
        # Slider velocity calculation
        # v_slider = r * ω * [sin(θ) + (r*sin(θ)*cos(θ))/sqrt(l²-r²*sin²(θ))]
        r = self.crank_length
        l = self.connecting_rod_length
        theta = crank_angle
        omega = crank_velocity
        
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        
        # Check for valid configuration
        denominator = math.sqrt(l**2 - r**2 * sin_theta**2)
        if denominator == 0:
            return {'success': False, 'error': 'Singular configuration'}
        
        slider_velocity = r * omega * (sin_theta + (r * sin_theta * cos_theta) / denominator)
        
        # Connecting rod angular velocity
        rod_angular_velocity = -r * omega * cos_theta / denominator
        
        return {
            'success': True,
            'crank_velocity': crank_velocity,
            'slider_velocity': slider_velocity,
            'connecting_rod_angular_velocity': rod_angular_velocity
        }


class SixBarLinkage:
    """
    Six-bar linkage mechanism.
    
    Can be either Watt or Stephenson type six-bar linkage.
    """
    
    def __init__(self, linkage_subtype: str = "watt", **kwargs):
        """
        Initialize six-bar linkage.
        
        Args:
            linkage_subtype: "watt" or "stephenson"
            **kwargs: Link lengths and configuration parameters
        """
        self.linkage_subtype = linkage_subtype
        self.link_lengths = kwargs
        
        if linkage_subtype == "watt":
            self._setup_watt_linkage()
        elif linkage_subtype == "stephenson":
            self._setup_stephenson_linkage()
        else:
            raise ValueError(f"Unknown six-bar subtype: {linkage_subtype}")
        
        logger.info(f"Six-bar {linkage_subtype} linkage created")
    
    def _setup_watt_linkage(self):
        """Setup Watt-type six-bar linkage."""
        # Watt linkage has two four-bar chains sharing a common link
        self.joints = [
            LinkageJoint("ground_1", (0, 0, 0), "fixed"),
            LinkageJoint("joint_1", (0, 0, 0), "revolute"),
            LinkageJoint("joint_2", (0, 0, 0), "revolute"),
            LinkageJoint("joint_3", (0, 0, 0), "revolute"),
            LinkageJoint("joint_4", (0, 0, 0), "revolute"),
            LinkageJoint("ground_2", (10, 0, 0), "fixed"),
        ]
        
        # Six links for Watt linkage
        self.links = [
            LinkageLink("ground", 10.0, "ground_1", "ground_2"),
            LinkageLink("link_1", 3.0, "ground_1", "joint_1"),
            LinkageLink("link_2", 8.0, "joint_1", "joint_2"),
            LinkageLink("link_3", 6.0, "joint_2", "joint_3"),
            LinkageLink("link_4", 4.0, "joint_3", "joint_4"),
            LinkageLink("link_5", 7.0, "joint_4", "ground_2"),
        ]
    
    def _setup_stephenson_linkage(self):
        """Setup Stephenson-type six-bar linkage."""
        # Stephenson linkage has a different topology
        self.joints = [
            LinkageJoint("ground_1", (0, 0, 0), "fixed"),
            LinkageJoint("joint_1", (0, 0, 0), "revolute"),
            LinkageJoint("joint_2", (0, 0, 0), "revolute"),
            LinkageJoint("joint_3", (0, 0, 0), "revolute"),
            LinkageJoint("joint_4", (0, 0, 0), "revolute"),
            LinkageJoint("ground_2", (12, 0, 0), "fixed"),
        ]
        
        self.links = [
            LinkageLink("ground", 12.0, "ground_1", "ground_2"),
            LinkageLink("link_1", 3.0, "ground_1", "joint_1"),
            LinkageLink("link_2", 9.0, "joint_1", "joint_2"),
            LinkageLink("link_3", 5.0, "joint_2", "joint_3"),
            LinkageLink("link_4", 7.0, "joint_3", "joint_4"),
            LinkageLink("link_5", 6.0, "joint_4", "ground_2"),
        ]
    
    def solve_positions(self, input_angle: float) -> Dict[str, Any]:
        """
        Solve position analysis for six-bar linkage.
        
        This is more complex than four-bar and requires iterative methods.
        """
        # Simplified implementation - full version would use numerical methods
        try:
            # For now, return a basic configuration
            joint_positions = [
                (0, 0, 0),      # Ground 1
                (2, 1, 0),      # Joint 1
                (4, 3, 0),      # Joint 2
                (6, 2, 0),      # Joint 3
                (8, 1, 0),      # Joint 4
                (10, 0, 0),     # Ground 2
            ]
            
            return {
                'success': True,
                'input_angle': input_angle,
                'joint_positions': joint_positions,
                'note': 'Six-bar analysis simplified - full implementation pending'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'joint_positions': [(0, 0, 0)] * 6
            }


def create_linkage(linkage_type: str, **parameters) -> object:
    """
    Factory function to create linkage mechanisms.
    
    Args:
        linkage_type: Type of linkage to create
        **parameters: Linkage-specific parameters
        
    Returns:
        Linkage mechanism object
    """
    if linkage_type == "four_bar":
        return FourBarLinkage(
            parameters['ground_length'],
            parameters['input_length'],
            parameters['coupler_length'],
            parameters['output_length']
        )
    elif linkage_type == "slider_crank":
        return SliderCrankMechanism(
            parameters['crank_length'],
            parameters['connecting_rod_length']
        )
    elif linkage_type == "six_bar":
        return SixBarLinkage(**parameters)
    else:
        raise ValueError(f"Unknown linkage type: {linkage_type}")


if __name__ == "__main__":
    # Test the linkage mechanisms
    print("Testing Four-Bar Linkage:")
    fourbar = FourBarLinkage(10.0, 3.0, 8.0, 5.0)
    grashof = fourbar.check_grashof_condition()
    print(f"Grashof condition: {grashof}")
    
    positions = fourbar.solve_positions(math.radians(45))
    print(f"Positions at 45°: {positions}")
    
    print("\nTesting Slider-Crank:")
    slider_crank = SliderCrankMechanism(2.0, 6.0)
    sc_positions = slider_crank.solve_positions(math.radians(90))
    print(f"Slider-crank at 90°: {sc_positions}") 