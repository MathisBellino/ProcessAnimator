#!/usr/bin/env python3
"""
Blender Auto-Setup for Multi-Bar Linkage Animation

Automatically creates:
- Armatures and bone hierarchies
- Constraint systems for linkages
- Visual representations
- Animation-ready rigs
"""

import math
import logging
from typing import Dict, Any, List, Tuple, Optional

try:
    import bpy
    import bmesh
    import mathutils
    from mathutils import Vector, Matrix, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: Blender not available. Running in simulation mode.")

logger = logging.getLogger(__name__)


class BlenderAutoSetup:
    """
    Automatic Blender setup for linkage mechanisms.
    
    Creates complete, animation-ready rigs with proper constraints
    and bone hierarchies for various linkage types.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Blender auto-setup.
        
        Args:
            config: Optional configuration for setup parameters
        """
        self.config = config or self._default_config()
        self.created_objects = []
        self.linkage_registry = {}
        
        if BLENDER_AVAILABLE:
            logger.info("Blender auto-setup initialized")
        else:
            logger.warning("Blender not available - running in simulation mode")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for Blender setup."""
        return {
            'bone_size': 0.1,
            'link_thickness': 0.05,
            'joint_size': 0.08,
            'constraint_visualization': True,
            'create_visual_mesh': True,
            'use_custom_shapes': True,
            'auto_ik_setup': True,
            'ground_material_color': (0.3, 0.3, 0.3, 1.0),
            'link_material_color': (0.2, 0.6, 0.8, 1.0),
            'joint_material_color': (0.8, 0.3, 0.2, 1.0),
            'motion_path_color': (0.9, 0.9, 0.1, 0.8)
        }
    
    def create_linkage_armature(self, linkage_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete armature for a linkage mechanism.
        
        Args:
            linkage_config: Configuration for the linkage
            
        Returns:
            Dictionary with creation results
        """
        if not BLENDER_AVAILABLE:
            return self._simulate_armature_creation(linkage_config)
        
        try:
            linkage_type = linkage_config['type']
            name = linkage_config.get('name', f'{linkage_type}_linkage')
            
            # Clear selection
            bpy.ops.object.select_all(action='DESELECT')
            
            # Create armature based on type
            if linkage_type == 'four_bar':
                result = self._create_four_bar_armature(linkage_config)
            elif linkage_type == 'slider_crank':
                result = self._create_slider_crank_armature(linkage_config)
            elif linkage_type == 'six_bar':
                result = self._create_six_bar_armature(linkage_config)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported linkage type: {linkage_type}'
                }
            
            if result['success']:
                armature_obj = result['armature_object']
                
                # Apply materials and visual enhancements
                self._apply_linkage_materials(armature_obj, linkage_config)
                
                # Setup constraints
                constraint_result = self._setup_linkage_constraints(armature_obj, linkage_config)
                
                # Create visual mesh if requested
                if self.config['create_visual_mesh']:
                    mesh_result = self._create_linkage_mesh(armature_obj, linkage_config)
                    result['visual_mesh'] = mesh_result
                
                # Store linkage information
                self.linkage_registry[armature_obj.name] = {
                    'config': linkage_config,
                    'constraints': constraint_result,
                    'created_time': bpy.context.scene.frame_current
                }
                
                result['constraint_setup'] = constraint_result
                
                logger.info(f"Successfully created {linkage_type} armature: {name}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to create linkage armature: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_four_bar_armature(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create armature for four-bar linkage."""
        from ..core.linkage_mechanisms import FourBarLinkage
        
        # Create linkage mechanism for calculations
        linkage = FourBarLinkage(
            config['ground_length'],
            config['input_length'],
            config['coupler_length'],
            config['output_length']
        )
        
        # Create armature object
        bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
        armature_obj = bpy.context.active_object
        armature_obj.name = config['name']
        armature_data = armature_obj.data
        armature_data.name = config['name'] + '_armature'
        
        # Remove default bone
        armature_data.edit_bones.remove(armature_data.edit_bones[0])
        
        # Calculate initial joint positions
        initial_positions = linkage.solve_positions(0)  # 0 degree input
        if not initial_positions['success']:
            return {'success': False, 'error': 'Failed to calculate initial positions'}
        
        joint_positions = initial_positions['joint_positions']
        
        # Create bones for each link
        bones = {}
        
        # Ground link (fixed)
        ground_bone = armature_data.edit_bones.new('ground_link')
        ground_bone.head = Vector(joint_positions[0])
        ground_bone.tail = Vector(joint_positions[3])
        bones['ground'] = ground_bone
        
        # Input link (driver)
        input_bone = armature_data.edit_bones.new('input_link')
        input_bone.head = Vector(joint_positions[0])
        input_bone.tail = Vector(joint_positions[1])
        bones['input'] = input_bone
        
        # Coupler link
        coupler_bone = armature_data.edit_bones.new('coupler_link')
        coupler_bone.head = Vector(joint_positions[1])
        coupler_bone.tail = Vector(joint_positions[2])
        bones['coupler'] = coupler_bone
        
        # Output link (follower)
        output_bone = armature_data.edit_bones.new('output_link')
        output_bone.head = Vector(joint_positions[2])
        output_bone.tail = Vector(joint_positions[3])
        bones['output'] = output_bone
        
        # Set bone relationships and properties
        # Input bone is the parent for the mechanism motion
        coupler_bone.parent = input_bone
        coupler_bone.use_connect = False
        
        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Set bone display properties
        armature_data.display_type = 'STICK'
        armature_data.show_names = True
        
        return {
            'success': True,
            'armature_object': armature_obj,
            'bone_names': list(bones.keys()),
            'linkage_mechanism': linkage
        }
    
    def _create_slider_crank_armature(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create armature for slider-crank mechanism."""
        from ..core.linkage_mechanisms import SliderCrankMechanism
        
        # Create linkage mechanism
        linkage = SliderCrankMechanism(
            config['crank_length'],
            config['connecting_rod_length']
        )
        
        # Create armature
        bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
        armature_obj = bpy.context.active_object
        armature_obj.name = config['name']
        armature_data = armature_obj.data
        armature_data.name = config['name'] + '_armature'
        
        # Remove default bone
        armature_data.edit_bones.remove(armature_data.edit_bones[0])
        
        # Calculate initial positions
        initial_positions = linkage.solve_positions(0)
        joint_positions = initial_positions['joint_positions']
        
        # Create bones
        bones = {}
        
        # Crank bone
        crank_bone = armature_data.edit_bones.new('crank')
        crank_bone.head = Vector(joint_positions[0])  # Crank center
        crank_bone.tail = Vector(joint_positions[1])  # Crank pin
        bones['crank'] = crank_bone
        
        # Connecting rod bone
        rod_bone = armature_data.edit_bones.new('connecting_rod')
        rod_bone.head = Vector(joint_positions[1])  # Crank pin
        rod_bone.tail = Vector(joint_positions[2])  # Slider
        bones['connecting_rod'] = rod_bone
        
        # Slider guide bone (for constraint visualization)
        slider_guide = armature_data.edit_bones.new('slider_guide')
        slider_guide.head = Vector((joint_positions[2][0] - 1, 0, 0))
        slider_guide.tail = Vector((joint_positions[2][0] + 1, 0, 0))
        bones['slider_guide'] = slider_guide
        
        # Set bone relationships
        rod_bone.parent = crank_bone
        rod_bone.use_connect = True
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Set display properties
        armature_data.display_type = 'STICK'
        armature_data.show_names = True
        
        return {
            'success': True,
            'armature_object': armature_obj,
            'bone_names': list(bones.keys()),
            'linkage_mechanism': linkage
        }
    
    def _create_six_bar_armature(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create armature for six-bar linkage."""
        # Simplified six-bar implementation
        bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
        armature_obj = bpy.context.active_object
        armature_obj.name = config['name']
        armature_data = armature_obj.data
        
        # Remove default bone
        armature_data.edit_bones.remove(armature_data.edit_bones[0])
        
        # Create 6 bones for six-bar linkage (simplified)
        bone_names = ['ground', 'link1', 'link2', 'link3', 'link4', 'link5']
        bones = {}
        
        # Create bones in a simple configuration
        for i, name in enumerate(bone_names):
            bone = armature_data.edit_bones.new(name)
            bone.head = Vector((i * 2, 0, 0))
            bone.tail = Vector((i * 2 + 1.5, 1, 0))
            bones[name] = bone
        
        bpy.ops.object.mode_set(mode='OBJECT')
        armature_data.display_type = 'STICK'
        
        return {
            'success': True,
            'armature_object': armature_obj,
            'bone_names': list(bones.keys()),
            'note': 'Six-bar implementation simplified'
        }
    
    def _setup_linkage_constraints(self, armature_obj: object, 
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup constraints for linkage mechanism."""
        if not BLENDER_AVAILABLE:
            return {'constraints_created': 0}
        
        # Switch to pose mode for constraint setup
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='POSE')
        
        constraints_created = 0
        constraint_details = []
        
        try:
            linkage_type = config['type']
            pose_bones = armature_obj.pose.bones
            
            if linkage_type == 'four_bar':
                constraints_created = self._setup_four_bar_constraints(pose_bones, config)
            elif linkage_type == 'slider_crank':
                constraints_created = self._setup_slider_crank_constraints(pose_bones, config)
            
            # Create constraint targets if needed
            if self.config['constraint_visualization']:
                self._create_constraint_targets(armature_obj, config)
            
            return {
                'constraints_created': constraints_created,
                'constraint_details': constraint_details,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to setup constraints: {e}")
            return {
                'constraints_created': 0,
                'success': False,
                'error': str(e)
            }
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
    
    def _setup_four_bar_constraints(self, pose_bones, config: Dict[str, Any]) -> int:
        """Setup constraints for four-bar linkage."""
        constraints_created = 0
        
        # IK constraint for coupler to maintain connection to output
        if 'coupler_link' in pose_bones and 'output_link' in pose_bones:
            coupler_bone = pose_bones['coupler_link']
            
            # Add IK constraint
            ik_constraint = coupler_bone.constraints.new(type='IK')
            ik_constraint.name = "Coupler_IK"
            ik_constraint.chain_count = 1
            ik_constraint.use_tail = True
            
            # Create target empty for IK
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(config['ground_length'], 1, 0))
            ik_target = bpy.context.active_object
            ik_target.name = f"{config['name']}_ik_target"
            
            ik_constraint.target = ik_target
            constraints_created += 1
        
        # Limit rotation for input link
        if 'input_link' in pose_bones:
            input_bone = pose_bones['input_link']
            
            # Add rotation limit
            limit_rot = input_bone.constraints.new(type='LIMIT_ROTATION')
            limit_rot.name = "Input_Rotation_Limit"
            limit_rot.use_limit_z = True
            limit_rot.min_z = 0
            limit_rot.max_z = math.radians(360)
            limit_rot.owner_space = 'LOCAL'
            constraints_created += 1
        
        return constraints_created
    
    def _setup_slider_crank_constraints(self, pose_bones, config: Dict[str, Any]) -> int:
        """Setup constraints for slider-crank mechanism."""
        constraints_created = 0
        
        # Crank rotation constraint
        if 'crank' in pose_bones:
            crank_bone = pose_bones['crank']
            
            limit_rot = crank_bone.constraints.new(type='LIMIT_ROTATION')
            limit_rot.name = "Crank_Rotation"
            limit_rot.use_limit_z = True
            limit_rot.min_z = 0
            limit_rot.max_z = math.radians(360)
            constraints_created += 1
        
        # Slider constraint for linear motion
        if 'connecting_rod' in pose_bones:
            rod_bone = pose_bones['connecting_rod']
            
            # IK constraint to maintain slider on X-axis
            ik_constraint = rod_bone.constraints.new(type='IK')
            ik_constraint.name = "Slider_IK"
            ik_constraint.chain_count = 1
            
            # Create slider target
            bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(5, 0, 0))
            slider_target = bpy.context.active_object
            slider_target.name = f"{config['name']}_slider_target"
            
            # Lock slider to X-axis only
            slider_target.lock_location[1] = True
            slider_target.lock_location[2] = True
            slider_target.lock_rotation[0] = True
            slider_target.lock_rotation[1] = True
            slider_target.lock_rotation[2] = True
            
            ik_constraint.target = slider_target
            constraints_created += 1
        
        return constraints_created
    
    def _create_constraint_targets(self, armature_obj: object, config: Dict[str, Any]):
        """Create visual targets for constraints."""
        # Create a collection for constraint targets
        collection_name = f"{config['name']}_targets"
        
        if collection_name not in bpy.data.collections:
            target_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(target_collection)
        else:
            target_collection = bpy.data.collections[collection_name]
        
        # Move existing targets to collection
        for obj in bpy.context.scene.objects:
            if obj.name.endswith('_target') and armature_obj.name in obj.name:
                if obj.name not in target_collection.objects:
                    target_collection.objects.link(obj)
                    if obj.name in bpy.context.scene.collection.objects:
                        bpy.context.scene.collection.objects.unlink(obj)
    
    def _create_linkage_mesh(self, armature_obj: object, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create visual mesh representation of the linkage."""
        try:
            # Create mesh objects for each link
            mesh_objects = []
            
            for bone in armature_obj.data.bones:
                if 'guide' not in bone.name.lower():  # Skip guide bones
                    mesh_obj = self._create_link_mesh(bone, config)
                    if mesh_obj:
                        mesh_objects.append(mesh_obj)
                        
                        # Parent mesh to armature
                        mesh_obj.parent = armature_obj
                        mesh_obj.parent_type = 'BONE'
                        mesh_obj.parent_bone = bone.name
            
            return {
                'success': True,
                'mesh_objects': mesh_objects,
                'count': len(mesh_objects)
            }
            
        except Exception as e:
            logger.error(f"Failed to create linkage mesh: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_link_mesh(self, bone, config: Dict[str, Any]) -> object:
        """Create mesh object for a single link."""
        bone_length = bone.length
        thickness = self.config['link_thickness']
        
        # Create cylinder mesh for the link
        bpy.ops.mesh.primitive_cylinder_add(
            radius=thickness,
            depth=bone_length,
            location=bone.head_local + (bone.tail_local - bone.head_local) / 2
        )
        
        mesh_obj = bpy.context.active_object
        mesh_obj.name = f"{config['name']}_mesh_{bone.name}"
        
        # Rotate to align with bone
        bone_vector = bone.tail_local - bone.head_local
        if bone_vector.length > 0:
            # Align cylinder with bone direction
            mesh_obj.rotation_euler = bone_vector.to_track_quat('Z', 'Y').to_euler()
        
        return mesh_obj
    
    def _apply_linkage_materials(self, armature_obj: object, config: Dict[str, Any]):
        """Apply materials to linkage components."""
        # Create materials for different link types
        materials = {}
        
        # Ground link material
        ground_mat = bpy.data.materials.new(name=f"{config['name']}_ground_material")
        ground_mat.use_nodes = True
        ground_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = self.config['ground_material_color']
        materials['ground'] = ground_mat
        
        # Link material
        link_mat = bpy.data.materials.new(name=f"{config['name']}_link_material")
        link_mat.use_nodes = True
        link_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = self.config['link_material_color']
        materials['link'] = link_mat
        
        # Apply materials to mesh objects
        for obj in bpy.context.scene.objects:
            if obj.parent == armature_obj and obj.type == 'MESH':
                if 'ground' in obj.name.lower():
                    obj.data.materials.append(ground_mat)
                else:
                    obj.data.materials.append(link_mat)
    
    def _simulate_armature_creation(self, linkage_config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate armature creation when Blender is not available."""
        return {
            'success': True,
            'armature_object': None,
            'simulation_mode': True,
            'linkage_type': linkage_config['type'],
            'name': linkage_config['name'],
            'note': 'Simulated creation - Blender not available'
        }
    
    def get_created_objects(self) -> List[str]:
        """Get list of all objects created by this setup instance."""
        return self.created_objects.copy()
    
    def cleanup_linkage(self, linkage_name: str) -> Dict[str, Any]:
        """Clean up all objects associated with a linkage."""
        if not BLENDER_AVAILABLE:
            return {'success': True, 'note': 'Simulation mode - no cleanup needed'}
        
        objects_removed = []
        
        # Remove armature and associated objects
        for obj in bpy.context.scene.objects:
            if linkage_name in obj.name:
                bpy.data.objects.remove(obj, do_unlink=True)
                objects_removed.append(obj.name)
        
        # Remove from registry
        if linkage_name in self.linkage_registry:
            del self.linkage_registry[linkage_name]
        
        return {
            'success': True,
            'objects_removed': objects_removed,
            'count': len(objects_removed)
        }


if __name__ == "__main__":
    # Test the auto-setup system
    if BLENDER_AVAILABLE:
        print("Testing Blender Auto-Setup:")
        
        setup = BlenderAutoSetup()
        
        # Test four-bar linkage creation
        four_bar_config = {
            'type': 'four_bar',
            'ground_length': 10.0,
            'input_length': 3.0,
            'coupler_length': 8.0,
            'output_length': 5.0,
            'name': 'TestFourBar'
        }
        
        result = setup.create_linkage_armature(four_bar_config)
        print(f"Four-bar creation result: {result}")
        
    else:
        print("Blender not available - skipping tests") 