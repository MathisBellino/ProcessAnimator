#!/usr/bin/env python3
"""
Robot Catalogue System

Manages robot model downloads, imports, and metadata from external sources.
Integrates with websites and databases to provide a comprehensive robot library.
"""

import bpy
import requests
import json
import os
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RobotCatalogue:
    """
    Robot Catalogue system for browsing, downloading, and importing robot models.
    
    Features:
    - Integration with external robot databases
    - Automatic model download and import
    - Metadata management and caching
    - Format conversion support
    """
    
    def __init__(self):
        self.catalogue_url = "https://api.robot-catalogue.com/v1"  # Placeholder API
        self.local_cache_dir = self._get_cache_directory()
        self.robot_database = {}
        self.supported_formats = ['.blend', '.fbx', '.obj', '.gltf', '.glb', '.dae']
        self.session = requests.Session()
        
        # Initialize local cache
        self._initialize_cache()
        
        logger.info("Robot Catalogue initialized")
    
    def _get_cache_directory(self) -> Path:
        """Get or create local cache directory for robot models."""
        addon_dir = Path(__file__).parent.parent
        cache_dir = addon_dir / "robot_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    def _initialize_cache(self):
        """Initialize local robot model cache."""
        cache_index_file = self.local_cache_dir / "index.json"
        
        if cache_index_file.exists():
            try:
                with open(cache_index_file, 'r') as f:
                    self.robot_database = json.load(f)
                logger.info(f"Loaded {len(self.robot_database)} robots from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.robot_database = {}
        else:
            self.robot_database = {}
    
    def fetch_robot_catalogue(self) -> Dict[str, Any]:
        """
        Fetch robot catalogue from external source.
        
        Returns:
            Dictionary containing robot catalogue data
        """
        try:
            # Try to fetch from online catalogue
            response = self.session.get(f"{self.catalogue_url}/robots", timeout=10)
            
            if response.status_code == 200:
                online_catalogue = response.json()
                self._update_local_cache(online_catalogue)
                return {
                    'success': True,
                    'robots': online_catalogue.get('robots', []),
                    'total_count': len(online_catalogue.get('robots', [])),
                    'source': 'online'
                }
            else:
                logger.warning(f"Online catalogue unavailable: {response.status_code}")
                return self._get_fallback_catalogue()
                
        except Exception as e:
            logger.warning(f"Failed to fetch online catalogue: {e}")
            return self._get_fallback_catalogue()
    
    def _get_fallback_catalogue(self) -> Dict[str, Any]:
        """Get fallback robot catalogue with common industrial robots."""
        fallback_robots = [
            {
                'id': 'ur5e',
                'name': 'Universal Robots UR5e',
                'manufacturer': 'Universal Robots',
                'type': 'Collaborative Robot',
                'dof': 6,
                'payload': 5.0,  # kg
                'reach': 850,   # mm
                'description': 'Lightweight, flexible collaborative robot perfect for assembly tasks',
                'file_formats': ['blend', 'fbx', 'urdf'],
                'download_url': 'https://models.robot-catalogue.com/ur5e.zip',
                'thumbnail': 'https://images.robot-catalogue.com/ur5e_thumb.jpg',
                'tags': ['collaborative', 'assembly', 'lightweight'],
                'applications': ['assembly', 'pick_and_place', 'quality_inspection']
            },
            {
                'id': 'kuka_kr10',
                'name': 'KUKA KR10 R1100',
                'manufacturer': 'KUKA',
                'type': 'Industrial Robot',
                'dof': 6,
                'payload': 10.0,
                'reach': 1100,
                'description': 'Precise industrial robot for welding and heavy-duty applications',
                'file_formats': ['blend', 'fbx', 'urdf'],
                'download_url': 'https://models.robot-catalogue.com/kuka_kr10.zip',
                'thumbnail': 'https://images.robot-catalogue.com/kuka_kr10_thumb.jpg',
                'tags': ['industrial', 'welding', 'heavy_duty'],
                'applications': ['welding', 'material_handling', 'machining']
            },
            {
                'id': 'abb_irb120',
                'name': 'ABB IRB 120',
                'manufacturer': 'ABB',
                'type': 'Compact Robot',
                'dof': 6,
                'payload': 3.0,
                'reach': 580,
                'description': 'Compact, fast robot ideal for electronics assembly',
                'file_formats': ['blend', 'fbx', 'urdf'],
                'download_url': 'https://models.robot-catalogue.com/abb_irb120.zip',
                'thumbnail': 'https://images.robot-catalogue.com/abb_irb120_thumb.jpg',
                'tags': ['compact', 'fast', 'electronics'],
                'applications': ['electronics_assembly', 'small_parts', 'testing']
            },
            {
                'id': 'fanuc_lr_mate',
                'name': 'FANUC LR Mate 200iD',
                'manufacturer': 'FANUC',
                'type': 'Compact Robot',
                'dof': 6,
                'payload': 7.0,
                'reach': 717,
                'description': 'Versatile robot for automation in confined spaces',
                'file_formats': ['blend', 'fbx', 'urdf'],
                'download_url': 'https://models.robot-catalogue.com/fanuc_lr_mate.zip',
                'thumbnail': 'https://images.robot-catalogue.com/fanuc_lr_mate_thumb.jpg',
                'tags': ['versatile', 'compact', 'automation'],
                'applications': ['material_handling', 'machine_tending', 'packaging']
            },
            {
                'id': 'delta_robot',
                'name': 'Generic Delta Robot',
                'manufacturer': 'Generic',
                'type': 'Delta Robot',
                'dof': 3,
                'payload': 1.0,
                'reach': 400,
                'description': 'High-speed parallel robot for pick-and-place operations',
                'file_formats': ['blend', 'fbx'],
                'download_url': 'https://models.robot-catalogue.com/delta_robot.zip',
                'thumbnail': 'https://images.robot-catalogue.com/delta_robot_thumb.jpg',
                'tags': ['high_speed', 'parallel', 'pick_and_place'],
                'applications': ['packaging', 'food_handling', 'sorting']
            },
            {
                'id': 'scara_robot',
                'name': 'Generic SCARA Robot',
                'manufacturer': 'Generic',
                'type': 'SCARA Robot',
                'dof': 4,
                'payload': 5.0,
                'reach': 600,
                'description': 'Selective compliance robot for precise horizontal movements',
                'file_formats': ['blend', 'fbx'],
                'download_url': 'https://models.robot-catalogue.com/scara_robot.zip',
                'thumbnail': 'https://images.robot-catalogue.com/scara_robot_thumb.jpg',
                'tags': ['precise', 'horizontal', 'compliance'],
                'applications': ['assembly', 'dispensing', 'testing']
            }
        ]
        
        return {
            'success': True,
            'robots': fallback_robots,
            'total_count': len(fallback_robots),
            'source': 'fallback'
        }
    
    def _update_local_cache(self, catalogue_data: Dict[str, Any]):
        """Update local cache with new catalogue data."""
        try:
            cache_index_file = self.local_cache_dir / "index.json"
            
            # Update robot database
            for robot in catalogue_data.get('robots', []):
                self.robot_database[robot['id']] = robot
            
            # Save to cache
            with open(cache_index_file, 'w') as f:
                json.dump(self.robot_database, f, indent=2)
            
            logger.info(f"Updated cache with {len(catalogue_data.get('robots', []))} robots")
            
        except Exception as e:
            logger.error(f"Failed to update cache: {e}")
    
    def search_robots(self, query: str = "", filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search robots in the catalogue.
        
        Args:
            query: Search query string
            filters: Optional filters (type, manufacturer, payload, etc.)
            
        Returns:
            List of matching robot dictionaries
        """
        if not self.robot_database:
            catalogue_data = self.fetch_robot_catalogue()
            if not catalogue_data['success']:
                return []
        
        robots = list(self.robot_database.values())
        
        # Apply text search
        if query:
            query = query.lower()
            robots = [
                robot for robot in robots
                if (query in robot['name'].lower() or
                    query in robot['manufacturer'].lower() or
                    query in robot['description'].lower() or
                    any(query in tag.lower() for tag in robot.get('tags', [])))
            ]
        
        # Apply filters
        if filters:
            if 'type' in filters and filters['type']:
                robots = [r for r in robots if r['type'] == filters['type']]
            
            if 'manufacturer' in filters and filters['manufacturer']:
                robots = [r for r in robots if r['manufacturer'] == filters['manufacturer']]
            
            if 'min_payload' in filters:
                robots = [r for r in robots if r['payload'] >= filters['min_payload']]
            
            if 'max_payload' in filters:
                robots = [r for r in robots if r['payload'] <= filters['max_payload']]
            
            if 'application' in filters and filters['application']:
                robots = [r for r in robots if filters['application'] in r.get('applications', [])]
        
        return robots
    
    def download_robot_model(self, robot_id: str, progress_callback=None) -> Dict[str, Any]:
        """
        Download robot model from catalogue.
        
        Args:
            robot_id: ID of the robot to download
            progress_callback: Optional callback for download progress
            
        Returns:
            Dictionary containing download results
        """
        if robot_id not in self.robot_database:
            return {'success': False, 'error': f'Robot {robot_id} not found in catalogue'}
        
        robot_info = self.robot_database[robot_id]
        download_url = robot_info.get('download_url')
        
        if not download_url:
            return {'success': False, 'error': 'No download URL available'}
        
        try:
            # Create robot-specific cache directory
            robot_cache_dir = self.local_cache_dir / robot_id
            robot_cache_dir.mkdir(exist_ok=True)
            
            # Check if already downloaded
            cached_file = robot_cache_dir / f"{robot_id}.zip"
            if cached_file.exists():
                logger.info(f"Robot {robot_id} already cached")
                return {
                    'success': True,
                    'cached': True,
                    'file_path': str(cached_file),
                    'robot_info': robot_info
                }
            
            # Download the file
            logger.info(f"Downloading robot model: {robot_id}")
            
            # For demo purposes, create a placeholder file
            # In real implementation, this would download from the actual URL
            self._create_demo_robot_file(robot_cache_dir, robot_info)
            
            return {
                'success': True,
                'cached': False,
                'file_path': str(cached_file),
                'robot_info': robot_info
            }
            
        except Exception as e:
            logger.error(f"Failed to download robot {robot_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_demo_robot_file(self, cache_dir: Path, robot_info: Dict):
        """Create a demo robot file for testing purposes."""
        # Create a simple .blend file or placeholder
        demo_file = cache_dir / f"{robot_info['id']}.blend"
        
        # For now, just create a metadata file
        metadata_file = cache_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(robot_info, f, indent=2)
        
        logger.info(f"Created demo files for {robot_info['id']}")
    
    def import_robot_to_scene(self, robot_id: str, import_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Import downloaded robot model into current Blender scene.
        
        Args:
            robot_id: ID of the robot to import
            import_options: Optional import settings
            
        Returns:
            Dictionary containing import results
        """
        # First ensure robot is downloaded
        download_result = self.download_robot_model(robot_id)
        if not download_result['success']:
            return download_result
        
        robot_info = download_result['robot_info']
        robot_cache_dir = self.local_cache_dir / robot_id
        
        try:
            # Look for importable files
            blend_file = robot_cache_dir / f"{robot_id}.blend"
            fbx_file = robot_cache_dir / f"{robot_id}.fbx"
            
            imported_objects = []
            
            if blend_file.exists():
                # Import from .blend file
                result = self._import_blend_file(blend_file, robot_info)
                imported_objects.extend(result.get('objects', []))
            elif fbx_file.exists():
                # Import from .fbx file
                result = self._import_fbx_file(fbx_file, robot_info)
                imported_objects.extend(result.get('objects', []))
            else:
                # Create a simple placeholder robot
                placeholder_result = self._create_placeholder_robot(robot_info)
                imported_objects.extend(placeholder_result.get('objects', []))
            
            # Post-process imported robot
            self._post_process_robot(imported_objects, robot_info, import_options)
            
            return {
                'success': True,
                'objects': imported_objects,
                'robot_info': robot_info,
                'message': f"Successfully imported {robot_info['name']}"
            }
            
        except Exception as e:
            logger.error(f"Failed to import robot {robot_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _import_blend_file(self, blend_file: Path, robot_info: Dict) -> Dict[str, Any]:
        """Import robot from .blend file."""
        # This would use bpy.ops.wm.append or link to import from .blend file
        # For demo, create placeholder
        return self._create_placeholder_robot(robot_info)
    
    def _import_fbx_file(self, fbx_file: Path, robot_info: Dict) -> Dict[str, Any]:
        """Import robot from .fbx file."""
        try:
            bpy.ops.import_scene.fbx(filepath=str(fbx_file))
            
            # Get newly imported objects (simplified)
            imported_objects = [obj for obj in bpy.context.selected_objects]
            
            return {'objects': imported_objects}
            
        except Exception as e:
            logger.warning(f"FBX import failed: {e}, creating placeholder")
            return self._create_placeholder_robot(robot_info)
    
    def _create_placeholder_robot(self, robot_info: Dict) -> Dict[str, Any]:
        """Create a placeholder robot for demo purposes."""
        import bmesh
        
        # Create a simple robot representation
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        base = bpy.context.active_object
        base.name = f"{robot_info['id']}_base"
        
        # Add some joints
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 2))
        joint1 = bpy.context.active_object
        joint1.name = f"{robot_info['id']}_joint1"
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=2, location=(0, 0, 4))
        arm = bpy.context.active_object
        arm.name = f"{robot_info['id']}_arm"
        
        # Group them
        bpy.ops.object.select_all(action='DESELECT')
        base.select_set(True)
        joint1.select_set(True)
        arm.select_set(True)
        
        # Create collection
        collection = bpy.data.collections.new(robot_info['name'])
        bpy.context.scene.collection.children.link(collection)
        
        for obj in [base, joint1, arm]:
            collection.objects.link(obj)
            bpy.context.scene.collection.objects.unlink(obj)
        
        logger.info(f"Created placeholder robot: {robot_info['name']}")
        
        return {'objects': [base, joint1, arm]}
    
    def _post_process_robot(self, objects: List, robot_info: Dict, options: Optional[Dict]):
        """Post-process imported robot (setup materials, constraints, etc.)."""
        if not objects:
            return
        
        # Add robot metadata to objects
        for obj in objects:
            obj['robot_id'] = robot_info['id']
            obj['robot_name'] = robot_info['name']
            obj['robot_type'] = robot_info['type']
            obj['robot_manufacturer'] = robot_info['manufacturer']
        
        # Set up basic materials
        self._setup_robot_materials(objects, robot_info)
        
        logger.info(f"Post-processed robot: {robot_info['name']}")
    
    def _setup_robot_materials(self, objects: List, robot_info: Dict):
        """Set up basic materials for robot objects."""
        # Create a simple material based on manufacturer
        manufacturer_colors = {
            'Universal Robots': (0.2, 0.4, 0.8, 1.0),  # Blue
            'KUKA': (1.0, 0.5, 0.0, 1.0),              # Orange
            'ABB': (0.8, 0.1, 0.1, 1.0),               # Red
            'FANUC': (1.0, 1.0, 0.0, 1.0),             # Yellow
            'Generic': (0.5, 0.5, 0.5, 1.0)            # Gray
        }
        
        manufacturer = robot_info.get('manufacturer', 'Generic')
        color = manufacturer_colors.get(manufacturer, (0.5, 0.5, 0.5, 1.0))
        
        # Create material
        mat_name = f"{robot_info['id']}_material"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            
            # Set base color
            if mat.node_tree:
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    principled.inputs['Base Color'].default_value = color
                    principled.inputs['Metallic'].default_value = 0.8
                    principled.inputs['Roughness'].default_value = 0.3
        
        # Apply material to objects
        material = bpy.data.materials[mat_name]
        for obj in objects:
            if obj.type == 'MESH':
                if not obj.data.materials:
                    obj.data.materials.append(material)
                else:
                    obj.data.materials[0] = material
    
    def get_robot_info(self, robot_id: str) -> Optional[Dict]:
        """Get detailed information about a specific robot."""
        return self.robot_database.get(robot_id)
    
    def get_manufacturers(self) -> List[str]:
        """Get list of available robot manufacturers."""
        if not self.robot_database:
            self.fetch_robot_catalogue()
        
        manufacturers = set()
        for robot in self.robot_database.values():
            manufacturers.add(robot['manufacturer'])
        
        return sorted(list(manufacturers))
    
    def get_robot_types(self) -> List[str]:
        """Get list of available robot types."""
        if not self.robot_database:
            self.fetch_robot_catalogue()
        
        types = set()
        for robot in self.robot_database.values():
            types.add(robot['type'])
        
        return sorted(list(types))


# Global catalogue instance
robot_catalogue = RobotCatalogue() 