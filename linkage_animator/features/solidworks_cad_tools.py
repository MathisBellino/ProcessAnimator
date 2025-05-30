#!/usr/bin/env python3
"""
SolidWorks-style CAD Tools for Blender

Implements SolidWorks-like interface for creating geometric primitives:
- Reference planes (Front, Top, Right)
- Sketch entities (lines, circles, arcs)
- Dimensions and constraints
- Feature tree navigation
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Euler
from bpy.types import Operator, Panel, PropertyGroup, Menu
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, EnumProperty, FloatVectorProperty
import logging

logger = logging.getLogger(__name__)


class SolidWorksCADManager:
    """
    Manager for SolidWorks-style CAD operations in Blender.
    """
    
    def __init__(self):
        self.reference_planes = {}
        self.sketch_entities = []
        self.dimensions = []
        self.feature_tree = []
        self.active_sketch = None
        
        # SolidWorks standard plane orientations
        self.standard_planes = {
            'Front': {'normal': (0, 1, 0), 'rotation': (90, 0, 0)},
            'Top': {'normal': (0, 0, 1), 'rotation': (0, 0, 0)},
            'Right': {'normal': (1, 0, 0), 'rotation': (0, 90, 0)}
        }
        
        logger.info("SolidWorks CAD Manager initialized")
    
    def create_reference_plane(self, name: str, location=(0, 0, 0), normal=(0, 0, 1), size=10.0):
        """Create a reference plane like in SolidWorks."""
        # Create plane mesh
        bpy.ops.mesh.primitive_plane_add(size=size, location=location)
        plane_obj = bpy.context.active_object
        plane_obj.name = f"RefPlane_{name}"
        
        # Set plane orientation
        if name in self.standard_planes:
            rotation = self.standard_planes[name]['rotation']
            plane_obj.rotation_euler = Euler([math.radians(r) for r in rotation], 'XYZ')
        
        # Set up plane properties
        plane_obj['is_reference_plane'] = True
        plane_obj['plane_name'] = name
        plane_obj['plane_type'] = 'reference'
        
        # Make plane wireframe and semi-transparent
        plane_obj.display_type = 'WIRE'
        
        # Create material for plane visualization
        mat_name = f"RefPlane_{name}_Mat"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            mat.blend_method = 'BLEND'
            
            if mat.node_tree:
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    # Set plane color based on standard
                    colors = {
                        'Front': (0.0, 1.0, 0.0, 0.3),  # Green
                        'Top': (0.0, 0.0, 1.0, 0.3),   # Blue
                        'Right': (1.0, 0.0, 0.0, 0.3)  # Red
                    }
                    color = colors.get(name, (0.7, 0.7, 0.7, 0.3))
                    principled.inputs['Base Color'].default_value = color
                    principled.inputs['Alpha'].default_value = color[3]
        
        # Apply material
        material = bpy.data.materials[mat_name]
        if not plane_obj.data.materials:
            plane_obj.data.materials.append(material)
        
        # Add to reference planes dictionary
        self.reference_planes[name] = plane_obj
        
        # Add to feature tree
        self.feature_tree.append({
            'type': 'plane',
            'name': name,
            'object': plane_obj,
            'children': []
        })
        
        return plane_obj
    
    def start_sketch(self, plane_obj):
        """Start a new sketch on the specified plane."""
        if not plane_obj or not plane_obj.get('is_reference_plane'):
            return None
        
        # Create sketch collection
        sketch_name = f"Sketch_{len(self.feature_tree) + 1}"
        sketch_collection = bpy.data.collections.new(sketch_name)
        bpy.context.scene.collection.children.link(sketch_collection)
        
        # Set active sketch
        self.active_sketch = {
            'name': sketch_name,
            'collection': sketch_collection,
            'plane': plane_obj,
            'entities': [],
            'constraints': [],
            'dimensions': []
        }
        
        # Switch to sketch mode (equivalent to Edit mode)
        bpy.context.view_layer.objects.active = plane_obj
        
        return self.active_sketch
    
    def create_sketch_line(self, start_point, end_point):
        """Create a line in the active sketch (SolidWorks style)."""
        if not self.active_sketch:
            return None
        
        # Create line using curve
        curve_data = bpy.data.curves.new(f'Line_{len(self.sketch_entities)}', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 1
        
        # Create spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(1)  # Add one more point (total 2)
        
        # Set points
        spline.points[0].co = (*start_point, 1)
        spline.points[1].co = (*end_point, 1)
        
        # Create object
        line_obj = bpy.data.objects.new(f'Line_{len(self.sketch_entities)}', curve_data)
        self.active_sketch['collection'].objects.link(line_obj)
        
        # Set line properties
        line_obj['sketch_entity'] = True
        line_obj['entity_type'] = 'line'
        line_obj['start_point'] = start_point
        line_obj['end_point'] = end_point
        
        # Style line for sketch appearance
        curve_data.bevel_depth = 0.02
        curve_data.fill_mode = 'FULL'
        
        # Add to sketch entities
        entity = {
            'type': 'line',
            'object': line_obj,
            'start_point': Vector(start_point),
            'end_point': Vector(end_point),
            'constraints': []
        }
        
        self.active_sketch['entities'].append(entity)
        self.sketch_entities.append(entity)
        
        return entity
    
    def create_sketch_circle(self, center_point, radius):
        """Create a circle in the active sketch (SolidWorks style)."""
        if not self.active_sketch:
            return None
        
        # Create circle using curve
        curve_data = bpy.data.curves.new(f'Circle_{len(self.sketch_entities)}', type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create spline
        spline = curve_data.splines.new('NURBS')
        spline.points.add(3)  # 4 points total for circle
        
        # Define circle points (approximation with 4 control points)
        angles = [0, 90, 180, 270]
        for i, angle in enumerate(angles):
            x = center_point[0] + radius * math.cos(math.radians(angle))
            y = center_point[1] + radius * math.sin(math.radians(angle))
            z = center_point[2]
            spline.points[i].co = (x, y, z, 1)
        
        spline.use_cyclic_u = True
        
        # Create object
        circle_obj = bpy.data.objects.new(f'Circle_{len(self.sketch_entities)}', curve_data)
        self.active_sketch['collection'].objects.link(circle_obj)
        
        # Set circle properties
        circle_obj['sketch_entity'] = True
        circle_obj['entity_type'] = 'circle'
        circle_obj['center_point'] = center_point
        circle_obj['radius'] = radius
        
        # Style circle
        curve_data.bevel_depth = 0.02
        
        # Add to entities
        entity = {
            'type': 'circle',
            'object': circle_obj,
            'center_point': Vector(center_point),
            'radius': radius,
            'constraints': []
        }
        
        self.active_sketch['entities'].append(entity)
        self.sketch_entities.append(entity)
        
        return entity
    
    def create_dimension(self, entity1, entity2=None, dimension_type='linear'):
        """Create dimension between sketch entities (SolidWorks style)."""
        if not self.active_sketch:
            return None
        
        dimension_name = f"Dim_{len(self.dimensions) + 1}"
        
        # Calculate dimension value
        if dimension_type == 'linear' and entity2:
            if entity1['type'] == 'line' and entity2['type'] == 'line':
                # Distance between parallel lines or length
                value = (entity1['end_point'] - entity1['start_point']).length
            else:
                value = 0.0
        elif dimension_type == 'radial' and entity1['type'] == 'circle':
            value = entity1['radius']
        elif dimension_type == 'diameter' and entity1['type'] == 'circle':
            value = entity1['radius'] * 2
        else:
            value = 1.0
        
        # Create dimension object (text object for display)
        bpy.ops.object.text_add()
        dim_obj = bpy.context.active_object
        dim_obj.name = dimension_name
        dim_obj.data.body = f"{value:.2f}"
        
        # Position dimension
        if entity1['type'] == 'line':
            midpoint = (entity1['start_point'] + entity1['end_point']) / 2
        elif entity1['type'] == 'circle':
            midpoint = entity1['center_point']
        else:
            midpoint = Vector((0, 0, 0))
        
        dim_obj.location = midpoint + Vector((0, 0, 0.5))  # Offset above
        
        # Set dimension properties
        dim_obj['is_dimension'] = True
        dim_obj['dimension_type'] = dimension_type
        dim_obj['dimension_value'] = value
        dim_obj['entity1'] = entity1['object']
        if entity2:
            dim_obj['entity2'] = entity2['object']
        
        # Style dimension text
        dim_obj.data.size = 0.5
        dim_obj.data.align_x = 'CENTER'
        dim_obj.data.align_y = 'CENTER'
        
        # Add to sketch collection
        self.active_sketch['collection'].objects.link(dim_obj)
        bpy.context.scene.collection.objects.unlink(dim_obj)
        
        dimension = {
            'name': dimension_name,
            'type': dimension_type,
            'value': value,
            'object': dim_obj,
            'entity1': entity1,
            'entity2': entity2
        }
        
        self.active_sketch['dimensions'].append(dimension)
        self.dimensions.append(dimension)
        
        return dimension
    
    def exit_sketch(self):
        """Exit sketch mode and finalize sketch."""
        if not self.active_sketch:
            return
        
        # Add sketch to feature tree
        self.feature_tree.append({
            'type': 'sketch',
            'name': self.active_sketch['name'],
            'collection': self.active_sketch['collection'],
            'entities': len(self.active_sketch['entities']),
            'dimensions': len(self.active_sketch['dimensions'])
        })
        
        # Clear active sketch
        self.active_sketch = None
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
    
    def create_standard_planes(self):
        """Create the three standard reference planes like SolidWorks."""
        planes = {}
        
        for plane_name, config in self.standard_planes.items():
            plane = self.create_reference_plane(
                plane_name,
                location=(0, 0, 0),
                normal=config['normal']
            )
            planes[plane_name] = plane
        
        return planes


# Import math for calculations
import math


class ROBOTANIM_OT_create_reference_plane(Operator):
    """Create SolidWorks-style reference plane"""
    bl_idname = "robotanim.create_reference_plane"
    bl_label = "Reference Plane"
    bl_description = "Create a reference plane for sketching"
    bl_options = {'REGISTER', 'UNDO'}
    
    plane_type: EnumProperty(
        name="Plane Type",
        items=[
            ('Front', "Front Plane", "Front reference plane (YZ)"),
            ('Top', "Top Plane", "Top reference plane (XY)"),
            ('Right', "Right Plane", "Right reference plane (XZ)"),
            ('Custom', "Custom Plane", "Custom reference plane"),
        ],
        default='Front'
    )
    
    plane_size: FloatProperty(
        name="Size",
        description="Size of the reference plane",
        default=10.0,
        min=0.1,
        max=100.0
    )
    
    def execute(self, context):
        # Get or create CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            bpy.types.Scene._cad_manager = SolidWorksCADManager()
        
        cad_manager = bpy.types.Scene._cad_manager
        
        # Create plane
        plane = cad_manager.create_reference_plane(
            self.plane_type,
            size=self.plane_size
        )
        
        self.report({'INFO'}, f"Created {self.plane_type} reference plane")
        return {'FINISHED'}


class ROBOTANIM_OT_start_sketch(Operator):
    """Start a new sketch on selected plane"""
    bl_idname = "robotanim.start_sketch"
    bl_label = "Start Sketch"
    bl_description = "Start a new sketch on the selected reference plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or not active_obj.get('is_reference_plane'):
            self.report({'ERROR'}, "Please select a reference plane first")
            return {'CANCELLED'}
        
        # Get CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            bpy.types.Scene._cad_manager = SolidWorksCADManager()
        
        cad_manager = bpy.types.Scene._cad_manager
        
        # Start sketch
        sketch = cad_manager.start_sketch(active_obj)
        
        if sketch:
            self.report({'INFO'}, f"Started sketch: {sketch['name']}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to start sketch")
            return {'CANCELLED'}


class ROBOTANIM_OT_sketch_line(Operator):
    """Create line in active sketch"""
    bl_idname = "robotanim.sketch_line"
    bl_label = "Sketch Line"
    bl_description = "Create a line in the active sketch"
    bl_options = {'REGISTER', 'UNDO'}
    
    start_point: FloatVectorProperty(
        name="Start Point",
        description="Start point of the line",
        default=(0.0, 0.0, 0.0),
        size=3
    )
    
    end_point: FloatVectorProperty(
        name="End Point",
        description="End point of the line",
        default=(1.0, 0.0, 0.0),
        size=3
    )
    
    def execute(self, context):
        # Get CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            self.report({'ERROR'}, "No active CAD session")
            return {'CANCELLED'}
        
        cad_manager = bpy.types.Scene._cad_manager
        
        if not cad_manager.active_sketch:
            self.report({'ERROR'}, "No active sketch. Start a sketch first.")
            return {'CANCELLED'}
        
        # Create line
        line = cad_manager.create_sketch_line(self.start_point, self.end_point)
        
        if line:
            length = (Vector(self.end_point) - Vector(self.start_point)).length
            self.report({'INFO'}, f"Created line (length: {length:.2f})")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to create line")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ROBOTANIM_OT_sketch_circle(Operator):
    """Create circle in active sketch"""
    bl_idname = "robotanim.sketch_circle"
    bl_label = "Sketch Circle"
    bl_description = "Create a circle in the active sketch"
    bl_options = {'REGISTER', 'UNDO'}
    
    center_point: FloatVectorProperty(
        name="Center",
        description="Center point of the circle",
        default=(0.0, 0.0, 0.0),
        size=3
    )
    
    radius: FloatProperty(
        name="Radius",
        description="Radius of the circle",
        default=1.0,
        min=0.01,
        max=100.0
    )
    
    def execute(self, context):
        # Get CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            self.report({'ERROR'}, "No active CAD session")
            return {'CANCELLED'}
        
        cad_manager = bpy.types.Scene._cad_manager
        
        if not cad_manager.active_sketch:
            self.report({'ERROR'}, "No active sketch. Start a sketch first.")
            return {'CANCELLED'}
        
        # Create circle
        circle = cad_manager.create_sketch_circle(self.center_point, self.radius)
        
        if circle:
            self.report({'INFO'}, f"Created circle (radius: {self.radius:.2f})")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to create circle")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ROBOTANIM_OT_add_dimension(Operator):
    """Add dimension to sketch entities"""
    bl_idname = "robotanim.add_dimension"
    bl_label = "Add Dimension"
    bl_description = "Add dimension to selected sketch entities"
    bl_options = {'REGISTER', 'UNDO'}
    
    dimension_type: EnumProperty(
        name="Dimension Type",
        items=[
            ('linear', "Linear", "Linear dimension"),
            ('radial', "Radial", "Radial dimension"),
            ('diameter', "Diameter", "Diameter dimension"),
            ('angular', "Angular", "Angular dimension"),
        ],
        default='linear'
    )
    
    def execute(self, context):
        # Get CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            self.report({'ERROR'}, "No active CAD session")
            return {'CANCELLED'}
        
        cad_manager = bpy.types.Scene._cad_manager
        
        if not cad_manager.active_sketch:
            self.report({'ERROR'}, "No active sketch")
            return {'CANCELLED'}
        
        # Get selected sketch entities
        selected_entities = []
        for entity in cad_manager.active_sketch['entities']:
            if entity['object'].select_get():
                selected_entities.append(entity)
        
        if not selected_entities:
            self.report({'ERROR'}, "Please select sketch entities to dimension")
            return {'CANCELLED'}
        
        # Create dimension
        entity1 = selected_entities[0]
        entity2 = selected_entities[1] if len(selected_entities) > 1 else None
        
        dimension = cad_manager.create_dimension(entity1, entity2, self.dimension_type)
        
        if dimension:
            self.report({'INFO'}, f"Added {self.dimension_type} dimension: {dimension['value']:.2f}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to create dimension")
            return {'CANCELLED'}


class ROBOTANIM_OT_exit_sketch(Operator):
    """Exit sketch mode"""
    bl_idname = "robotanim.exit_sketch"
    bl_label = "Exit Sketch"
    bl_description = "Exit sketch mode and finalize sketch"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            self.report({'ERROR'}, "No active CAD session")
            return {'CANCELLED'}
        
        cad_manager = bpy.types.Scene._cad_manager
        
        if not cad_manager.active_sketch:
            self.report({'INFO'}, "No active sketch to exit")
            return {'CANCELLED'}
        
        sketch_name = cad_manager.active_sketch['name']
        cad_manager.exit_sketch()
        
        self.report({'INFO'}, f"Exited sketch: {sketch_name}")
        return {'FINISHED'}


class ROBOTANIM_OT_create_standard_planes(Operator):
    """Create standard reference planes (Front, Top, Right)"""
    bl_idname = "robotanim.create_standard_planes"
    bl_label = "Standard Planes"
    bl_description = "Create Front, Top, and Right reference planes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get or create CAD manager
        if not hasattr(bpy.types.Scene, '_cad_manager'):
            bpy.types.Scene._cad_manager = SolidWorksCADManager()
        
        cad_manager = bpy.types.Scene._cad_manager
        planes = cad_manager.create_standard_planes()
        
        self.report({'INFO'}, f"Created {len(planes)} standard reference planes")
        return {'FINISHED'}


# Panel for SolidWorks-style CAD tools
class ROBOTANIM_PT_solidworks_cad(Panel):
    """SolidWorks-style CAD tools panel"""
    bl_label = "🔧 CAD Tools"
    bl_idname = "ROBOTANIM_PT_solidworks_cad"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot Studio"
    bl_parent_id = "ROBOTANIM_PT_complete_workflow"
    
    def draw(self, context):
        layout = self.layout
        
        # Get CAD manager status
        cad_manager = getattr(bpy.types.Scene, '_cad_manager', None)
        active_sketch = cad_manager.active_sketch if cad_manager else None
        
        # Header
        header_box = layout.box()
        header_box.label(text="SolidWorks-Style CAD Tools", icon='MODIFIER_ON')
        
        # Reference Planes section
        planes_box = layout.box()
        planes_box.label(text="📐 Reference Planes", icon='MESH_PLANE')
        
        # Quick standard planes
        planes_box.operator("robotanim.create_standard_planes", 
                           text="Create Standard Planes", 
                           icon='EMPTY_AXIS')
        
        # Individual plane creation
        plane_row = planes_box.row(align=True)
        op = plane_row.operator("robotanim.create_reference_plane", text="Front")
        op.plane_type = 'Front'
        op = plane_row.operator("robotanim.create_reference_plane", text="Top")
        op.plane_type = 'Top'
        op = plane_row.operator("robotanim.create_reference_plane", text="Right")
        op.plane_type = 'Right'
        
        layout.separator()
        
        # Sketch section
        sketch_box = layout.box()
        sketch_box.label(text="✏️ Sketching", icon='GREASEPENCIL')
        
        if active_sketch:
            # Active sketch mode
            sketch_box.alert = True
            sketch_box.label(text=f"Active: {active_sketch['name']}", icon='CHECKMARK')
            sketch_box.label(text=f"Entities: {len(active_sketch['entities'])}")
            sketch_box.label(text=f"Dimensions: {len(active_sketch['dimensions'])}")
            
            # Sketch tools
            tools_row = sketch_box.row(align=True)
            tools_row.operator("robotanim.sketch_line", text="Line", icon='IPO_LINEAR')
            tools_row.operator("robotanim.sketch_circle", text="Circle", icon='MESH_CIRCLE')
            
            # Dimension tools
            dim_box = sketch_box.box()
            dim_box.label(text="📏 Dimensions:")
            dim_box.operator("robotanim.add_dimension", text="Add Dimension", icon='DRIVER_DISTANCE')
            
            # Exit sketch
            sketch_box.separator()
            sketch_box.operator("robotanim.exit_sketch", 
                               text="Exit Sketch", 
                               icon='CHECKMARK')
        else:
            # Start sketch mode
            sketch_box.label(text="Select a reference plane, then:")
            sketch_box.operator("robotanim.start_sketch", 
                               text="Start Sketch", 
                               icon='GREASEPENCIL')
        
        layout.separator()
        
        # Feature tree
        tree_box = layout.box()
        tree_box.label(text="🌳 Feature Tree", icon='OUTLINER')
        
        if cad_manager and cad_manager.feature_tree:
            for i, feature in enumerate(cad_manager.feature_tree[-5:]):  # Show last 5
                row = tree_box.row()
                if feature['type'] == 'plane':
                    row.label(text=f"📐 {feature['name']}", icon='MESH_PLANE')
                elif feature['type'] == 'sketch':
                    row.label(text=f"✏️ {feature['name']} ({feature['entities']} entities)", icon='GREASEPENCIL')
                else:
                    row.label(text=f"🔧 {feature['name']}")
        else:
            tree_box.label(text="No features created yet")
        
        # Tips
        tips_box = layout.box()
        tips_box.label(text="💡 SolidWorks Workflow:", icon='INFO')
        tips_box.label(text="1. Create reference planes")
        tips_box.label(text="2. Start sketch on plane")
        tips_box.label(text="3. Draw lines, circles")
        tips_box.label(text="4. Add dimensions")
        tips_box.label(text="5. Exit sketch")


# Registration
solidworks_cad_classes = [
    ROBOTANIM_OT_create_reference_plane,
    ROBOTANIM_OT_start_sketch,
    ROBOTANIM_OT_sketch_line,
    ROBOTANIM_OT_sketch_circle,
    ROBOTANIM_OT_add_dimension,
    ROBOTANIM_OT_exit_sketch,
    ROBOTANIM_OT_create_standard_planes,
    ROBOTANIM_PT_solidworks_cad,
]


def register_solidworks_cad():
    """Register SolidWorks CAD classes."""
    for cls in solidworks_cad_classes:
        bpy.utils.register_class(cls)


def unregister_solidworks_cad():
    """Unregister SolidWorks CAD classes."""
    # Clean up CAD manager
    if hasattr(bpy.types.Scene, '_cad_manager'):
        delattr(bpy.types.Scene, '_cad_manager')
    
    # Unregister classes
    for cls in reversed(solidworks_cad_classes):
        bpy.utils.unregister_class(cls) 