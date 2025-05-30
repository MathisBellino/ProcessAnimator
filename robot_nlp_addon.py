bl_info = {
    "name": "Robot NLP Controller",
    "author": "Robot Animator Plus Delux 3000",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Robot NLP",
    "description": "Control robots with natural language using AI",
    "category": "Animation",
}

import bpy
import sys
import os
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty

# Add the robot_animator directory to Python path
addon_dir = os.path.dirname(os.path.realpath(__file__))
robot_animator_path = os.path.join(addon_dir, 'robot_animator')
if robot_animator_path not in sys.path:
    sys.path.insert(0, robot_animator_path)

try:
    from enhanced_nlp import EnhancedNLProcessor
    NLP_AVAILABLE = True
except ImportError as e:
    print(f"NLP not available: {e}")
    NLP_AVAILABLE = False

# Global NLP processor
nlp_processor = None

def initialize_nlp():
    """Initialize the NLP processor if available."""
    global nlp_processor
    if NLP_AVAILABLE and nlp_processor is None:
        try:
            nlp_processor = EnhancedNLProcessor()
            return True
        except Exception as e:
            print(f"Failed to initialize NLP: {e}")
            return False
    return nlp_processor is not None

class ROBOT_PT_nlp_panel(Panel):
    """Main panel for Robot NLP control."""
    bl_label = "🤖 Robot NLP Controller"
    bl_idname = "ROBOT_PT_nlp"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Status section
        box = layout.box()
        box.label(text="🧠 AI Status:", icon='INFO')
        
        if NLP_AVAILABLE:
            if nlp_processor is not None:
                box.label(text="✅ AI Ready", icon='CHECKMARK')
            else:
                box.label(text="⏳ Initializing...", icon='TIME')
                box.operator("robot.initialize_nlp", text="Initialize AI")
        else:
            box.label(text="❌ AI Not Available", icon='ERROR')
            box.label(text="Install dependencies first")
        
        layout.separator()
        
        # Command input section
        box = layout.box()
        box.label(text="💬 Natural Language Commands:", icon='SYNTAX_ON')
        
        # Text input for commands
        box.prop(scene.robot_nlp, "command", text="")
        
        # Quick command buttons
        row = box.row(align=True)
        row.operator("robot.quick_command", text="Pick Cube").command = "pick up the cube"
        row.operator("robot.quick_command", text="Move Corner").command = "move to the corner"
        
        row = box.row(align=True)
        row.operator("robot.quick_command", text="Grab Sphere").command = "grab the blue sphere"
        row.operator("robot.quick_command", text="Place Table").command = "place it on the table"
        
        # Execute button
        layout.separator()
        execute_row = layout.row()
        execute_row.scale_y = 2.0
        execute_row.operator("robot.execute_nlp_command", text="🚀 Execute Command", icon='PLAY')
        
        layout.separator()
        
        # Results section
        if hasattr(scene.robot_nlp, 'last_result') and scene.robot_nlp.last_result:
            box = layout.box()
            box.label(text="📋 Last Result:", icon='PRESET')
            
            # Show success status
            if scene.robot_nlp.last_success:
                box.label(text="✅ Success", icon='CHECKMARK')
            else:
                box.label(text="❌ Failed", icon='ERROR')
            
            # Show confidence
            box.label(text=f"🎯 Confidence: {scene.robot_nlp.last_confidence:.2f}")
            
            # Show intent
            box.label(text=f"🧠 Intent: {scene.robot_nlp.last_intent}")
            
            # Show actions
            if scene.robot_nlp.last_actions:
                box.label(text="🤖 Actions:")
                actions = scene.robot_nlp.last_actions.split('|')
                for i, action in enumerate(actions[:5], 1):  # Show max 5 actions
                    box.label(text=f"  {i}. {action}")

class ROBOT_OT_initialize_nlp(Operator):
    """Initialize the NLP processor."""
    bl_idname = "robot.initialize_nlp"
    bl_label = "Initialize NLP"
    bl_description = "Initialize the AI natural language processor"
    
    def execute(self, context):
        if initialize_nlp():
            self.report({'INFO'}, "AI initialized successfully!")
        else:
            self.report({'ERROR'}, "Failed to initialize AI")
        return {'FINISHED'}

class ROBOT_OT_quick_command(Operator):
    """Execute a predefined quick command."""
    bl_idname = "robot.quick_command"
    bl_label = "Quick Command"
    bl_description = "Execute a predefined command"
    
    command: StringProperty()
    
    def execute(self, context):
        context.scene.robot_nlp.command = self.command
        bpy.ops.robot.execute_nlp_command()
        return {'FINISHED'}

class ROBOT_OT_execute_nlp_command(Operator):
    """Execute the natural language command."""
    bl_idname = "robot.execute_nlp_command"
    bl_label = "Execute NLP Command"
    bl_description = "Process and execute the natural language command"
    
    def execute(self, context):
        scene = context.scene
        command = scene.robot_nlp.command.strip()
        
        if not command:
            self.report({'WARNING'}, "Please enter a command")
            return {'CANCELLED'}
        
        if not NLP_AVAILABLE:
            self.report({'ERROR'}, "AI not available. Install dependencies first.")
            return {'CANCELLED'}
        
        if nlp_processor is None:
            if not initialize_nlp():
                self.report({'ERROR'}, "Failed to initialize AI")
                return {'CANCELLED'}
        
        try:
            # Process the command
            result = nlp_processor.process_command(command)
            
            # Store results in scene properties
            scene.robot_nlp.last_result = True
            scene.robot_nlp.last_success = result['success']
            scene.robot_nlp.last_confidence = result['confidence']
            scene.robot_nlp.last_intent = result['parsed_command']['intent']
            
            # Format actions for display
            if result['actions']:
                actions_text = []
                for action in result['actions']:
                    if action['action'] == 'move_to':
                        actions_text.append(f"Move to {action['target']}")
                    elif action['action'] == 'grab':
                        actions_text.append(f"Grab {action['target']}")
                    elif action['action'] == 'place':
                        actions_text.append(f"Place {action['target']} on {action.get('location', 'location')}")
                    else:
                        actions_text.append(f"{action['action'].title()}: {action.get('target', 'N/A')}")
                
                scene.robot_nlp.last_actions = '|'.join(actions_text)
                
                # Execute the actions visually in Blender
                self.execute_visual_actions(result['actions'])
                
                self.report({'INFO'}, f"Executed {len(result['actions'])} actions with {result['confidence']:.2f} confidence")
            else:
                scene.robot_nlp.last_actions = "No actions generated"
                self.report({'WARNING'}, f"No actions generated. Confidence: {result['confidence']:.2f}")
        
        except Exception as e:
            self.report({'ERROR'}, f"Error processing command: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def execute_visual_actions(self, actions):
        """Execute actions visually in Blender (create/move objects)."""
        for action in actions:
            if action['action'] == 'move_to':
                self.create_or_move_object(action['target'], 'move')
            elif action['action'] == 'grab':
                self.create_or_move_object(action['target'], 'grab')
            elif action['action'] == 'place':
                self.create_or_move_object(action['target'], 'place', action.get('location'))
    
    def create_or_move_object(self, object_name, action_type, location=None):
        """Create or move objects in Blender to visualize the action."""
        try:
            # Clean up object name
            obj_name = object_name.replace('the ', '').replace('a ', '')
            
            # Check if object exists
            obj = bpy.data.objects.get(obj_name)
            
            if obj is None:
                # Create object based on name
                if 'cube' in obj_name.lower():
                    bpy.ops.mesh.primitive_cube_add()
                elif 'sphere' in obj_name.lower():
                    bpy.ops.mesh.primitive_uv_sphere_add()
                elif 'cylinder' in obj_name.lower():
                    bpy.ops.mesh.primitive_cylinder_add()
                else:
                    bpy.ops.mesh.primitive_cube_add()  # Default to cube
                
                obj = bpy.context.active_object
                obj.name = obj_name
                
                # Color based on name
                if 'red' in object_name.lower():
                    self.set_object_color(obj, (1, 0, 0, 1))  # Red
                elif 'blue' in object_name.lower():
                    self.set_object_color(obj, (0, 0, 1, 1))  # Blue
                elif 'green' in object_name.lower():
                    self.set_object_color(obj, (0, 1, 0, 1))  # Green
            
            # Move object based on action
            if action_type == 'move' or action_type == 'grab':
                # Simulate robot moving to object
                obj.location.z += 0.5  # Lift slightly
                
            elif action_type == 'place' and location:
                # Move to location
                if 'table' in location.lower():
                    obj.location = (2, 0, 1)
                elif 'shelf' in location.lower():
                    obj.location = (-2, 0, 2)
                elif 'corner' in location.lower():
                    obj.location = (3, 3, 0)
                else:
                    obj.location.x += 2  # Default move
            
        except Exception as e:
            print(f"Error creating/moving object: {e}")
    
    def set_object_color(self, obj, color):
        """Set the color of an object."""
        try:
            # Create material if it doesn't exist
            mat_name = f"{obj.name}_material"
            mat = bpy.data.materials.get(mat_name)
            
            if mat is None:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                # Set base color
                mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color
            
            # Assign material to object
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
                
        except Exception as e:
            print(f"Error setting color: {e}")

class RobotNLPProperties(PropertyGroup):
    """Properties for Robot NLP."""
    command: StringProperty(
        name="Command",
        description="Natural language command for the robot",
        default="pick up the red cube and place it on the table"
    )
    
    last_result: BoolProperty(default=False)
    last_success: BoolProperty(default=False)
    last_confidence: bpy.props.FloatProperty(default=0.0)
    last_intent: StringProperty(default="")
    last_actions: StringProperty(default="")

classes = [
    RobotNLPProperties,
    ROBOT_PT_nlp_panel,
    ROBOT_OT_initialize_nlp,
    ROBOT_OT_quick_command,
    ROBOT_OT_execute_nlp_command,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.robot_nlp = bpy.props.PointerProperty(type=RobotNLPProperties)
    
    # Try to initialize NLP on startup
    initialize_nlp()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.robot_nlp

if __name__ == "__main__":
    register() 