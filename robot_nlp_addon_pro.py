bl_info = {
    "name": "Robot NLP Controller Pro",
    "author": "Robot Animator Plus Delux 3000",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Robot NLP",
    "description": "Advanced Robot Control with AI-powered Natural Language Interface",
    "category": "Animation",
}

import bpy
import sys
import os
import json
import time
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty

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

# Global variables
nlp_processor = None
animation_queue = []
command_history = []

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

def log_command(command, result):
    """Log commands for history and analysis."""
    global command_history
    command_history.append({
        'timestamp': time.time(),
        'command': command,
        'success': result.get('success', False),
        'confidence': result.get('confidence', 0.0)
    })
    # Keep only last 20 commands
    if len(command_history) > 20:
        command_history = command_history[-20:]

class ROBOT_PT_main_panel(Panel):
    """Main Robot NLP control panel."""
    bl_label = "🤖 Robot NLP Controller Pro"
    bl_idname = "ROBOT_PT_nlp_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_pro
        
        # Header with status indicator
        header = layout.box()
        row = header.row()
        if NLP_AVAILABLE and nlp_processor is not None:
            row.label(text="🟢 AI READY", icon='CHECKMARK')
        elif NLP_AVAILABLE:
            row.label(text="🟡 INITIALIZING", icon='TIME')
        else:
            row.label(text="🔴 AI OFFLINE", icon='ERROR')
        
        row.operator("robot.open_settings", text="", icon='PREFERENCES')
        
        layout.separator()
        
        # Quick status bar
        status_box = layout.box()
        col = status_box.column(align=True)
        col.label(text=f"Commands Processed: {len(command_history)}")
        if command_history:
            last_confidence = command_history[-1].get('confidence', 0.0)
            col.label(text=f"Last Confidence: {last_confidence:.2f}")

class ROBOT_PT_command_panel(Panel):
    """Command input and execution panel."""
    bl_label = "💬 Natural Language Commands"
    bl_idname = "ROBOT_PT_command"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_nlp_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_pro
        
        # Command input section
        box = layout.box()
        box.label(text="Enter Command:", icon='SYNTAX_ON')
        box.prop(props, "command", text="")
        
        # Voice input toggle (placeholder for future feature)
        row = box.row(align=True)
        row.prop(props, "use_voice_input", text="🎤 Voice", toggle=True)
        row.prop(props, "auto_execute", text="🚀 Auto", toggle=True)
        
        # Execute button
        execute_row = layout.row()
        execute_row.scale_y = 1.5
        if props.command.strip():
            execute_row.operator("robot.execute_command", text="🚀 Execute Command", icon='PLAY')
        else:
            execute_row.enabled = False
            execute_row.operator("robot.execute_command", text="Enter Command First", icon='INFO')
        
        layout.separator()
        
        # Quick commands grid
        box = layout.box()
        box.label(text="⚡ Quick Commands:", icon='PRESET')
        
        # Basic commands
        col = box.column(align=True)
        col.label(text="Basic Actions:")
        row = col.row(align=True)
        row.operator("robot.quick_command", text="Pick Cube").command = "pick up the red cube"
        row.operator("robot.quick_command", text="Move Home").command = "move robot to home position"
        
        row = col.row(align=True)
        row.operator("robot.quick_command", text="Grab Sphere").command = "grab the blue sphere"
        row.operator("robot.quick_command", text="Place Table").command = "place it on the table"
        
        # Advanced commands
        col.separator()
        col.label(text="Advanced:")
        row = col.row(align=True)
        row.operator("robot.quick_command", text="Pick & Place").command = "pick up the cube and place it on the shelf"
        
        row = col.row(align=True)
        row.operator("robot.quick_command", text="Complex Task").command = "organize all objects by color on different tables"

class ROBOT_PT_animation_panel(Panel):
    """Animation preview and control panel."""
    bl_label = "🎬 Animation Preview"
    bl_idname = "ROBOT_PT_animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_nlp_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_pro
        
        box = layout.box()
        box.label(text="Animation Controls:", icon='PLAY')
        
        # Animation settings
        col = box.column(align=True)
        col.prop(props, "animation_speed", text="Speed")
        col.prop(props, "preview_mode", text="Preview")
        
        # Animation buttons
        row = box.row(align=True)
        row.operator("robot.preview_animation", text="👁️ Preview", icon='HIDE_OFF')
        row.operator("robot.create_keyframes", text="🔑 Keyframes", icon='KEYFRAME')
        
        # Timeline info
        if props.last_animation_frames > 0:
            box.separator()
            box.label(text=f"📊 Duration: {props.last_animation_frames} frames")
            box.label(text=f"⏱️ Time: {props.last_animation_frames/24:.1f}s @ 24fps")

class ROBOT_PT_results_panel(Panel):
    """Results and feedback panel."""
    bl_label = "📊 Results & Analysis"
    bl_idname = "ROBOT_PT_results"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_nlp_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_pro
        
        if not props.last_result:
            layout.label(text="No results yet. Execute a command first.", icon='INFO')
            return
            
        # Results box
        box = layout.box()
        
        # Success indicator
        if props.last_success:
            box.label(text="✅ SUCCESS", icon='CHECKMARK')
        else:
            box.label(text="❌ FAILED", icon='ERROR')
        
        # Confidence meter
        conf_row = box.row()
        conf_row.label(text="🎯 Confidence:")
        conf_bar = conf_row.row()
        conf_bar.scale_x = props.last_confidence
        if props.last_confidence >= 0.8:
            conf_bar.label(text="HIGH", icon='CHECKMARK')
        elif props.last_confidence >= 0.5:
            conf_bar.label(text="MEDIUM", icon='QUESTION') 
        else:
            conf_bar.label(text="LOW", icon='ERROR')
        
        box.label(text=f"📈 Score: {props.last_confidence:.3f}")
        
        # Intent and actions
        if props.last_intent:
            box.separator()
            box.label(text=f"🧠 Intent: {props.last_intent}")
        
        if props.last_actions:
            box.separator()
            box.label(text="🤖 Generated Actions:")
            actions = props.last_actions.split('|')
            for i, action in enumerate(actions[:5], 1):
                box.label(text=f"  {i}. {action}")

class ROBOT_PT_settings_panel(Panel):
    """Advanced settings panel."""
    bl_label = "⚙️ Advanced Settings"
    bl_idname = "ROBOT_PT_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_nlp_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_pro
        
        box = layout.box()
        box.label(text="AI Configuration:", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(props, "confidence_threshold", text="Min Confidence")
        col.prop(props, "safety_mode", text="Safety Mode")
        col.prop(props, "debug_mode", text="Debug Output")
        
        box.separator()
        box.operator("robot.reset_settings", text="🔄 Reset to Defaults")
        
        # System info
        info_box = layout.box()
        info_box.label(text="System Info:", icon='INFO')
        info_box.label(text=f"NLP Available: {'✅' if NLP_AVAILABLE else '❌'}")
        info_box.label(text=f"Commands in History: {len(command_history)}")
        
        if command_history:
            success_rate = sum(1 for cmd in command_history if cmd['success']) / len(command_history)
            info_box.label(text=f"Success Rate: {success_rate:.1%}")

# Operators
class ROBOT_OT_execute_command(Operator):
    """Execute the natural language command."""
    bl_idname = "robot.execute_command"
    bl_label = "Execute Command"
    bl_description = "Process and execute the natural language command"
    
    def execute(self, context):
        scene = context.scene
        props = scene.robot_nlp_pro
        command = props.command.strip()
        
        if not command:
            self.report({'WARNING'}, "Please enter a command")
            return {'CANCELLED'}
        
        # Safety check
        if props.safety_mode and self.is_unsafe_command(command):
            self.report({'ERROR'}, "Command blocked by safety mode")
            return {'CANCELLED'}
        
        if not NLP_AVAILABLE:
            self.report({'ERROR'}, "AI not available. Check installation.")
            return {'CANCELLED'}
        
        if nlp_processor is None:
            if not initialize_nlp():
                self.report({'ERROR'}, "Failed to initialize AI")
                return {'CANCELLED'}
        
        try:
            # Process the command
            self.report({'INFO'}, f"Processing: {command}")
            result = nlp_processor.process_command(command)
            
            # Check confidence threshold
            if result['confidence'] < props.confidence_threshold:
                self.report({'WARNING'}, f"Low confidence ({result['confidence']:.2f}). Adjust threshold or rephrase.")
                return {'CANCELLED'}
            
            # Store results
            props.last_result = True
            props.last_success = result['success']
            props.last_confidence = result['confidence']
            props.last_intent = result['parsed_command']['intent']
            
            # Log command
            log_command(command, result)
            
            # Format and execute actions
            if result['actions']:
                actions_text = []
                total_frames = 0
                
                for action in result['actions']:
                    action_desc = self.format_action(action)
                    actions_text.append(action_desc)
                    total_frames += 30  # Estimate 30 frames per action
                
                props.last_actions = '|'.join(actions_text)
                props.last_animation_frames = total_frames
                
                # Execute visual actions
                self.execute_visual_actions(result['actions'])
                
                success_msg = f"✅ Executed {len(result['actions'])} actions"
                conf_msg = f"Confidence: {result['confidence']:.2f}"
                self.report({'INFO'}, f"{success_msg} | {conf_msg}")
                
            else:
                props.last_actions = "No actions generated"
                self.report({'WARNING'}, "No executable actions found")
        
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.report({'ERROR'}, error_msg)
            if props.debug_mode:
                print(f"Debug: {error_msg}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def is_unsafe_command(self, command):
        """Check if command contains unsafe keywords."""
        unsafe_keywords = ['fast', 'quickly', 'throw', 'slam', 'crash', 'hit', 'break']
        return any(keyword in command.lower() for keyword in unsafe_keywords)
    
    def format_action(self, action):
        """Format action for display."""
        if action['action'] == 'move_to':
            return f"Move to {action['target']}"
        elif action['action'] == 'grab':
            return f"Grab {action['target']}"
        elif action['action'] == 'place':
            location = action.get('location', 'location')
            return f"Place {action['target']} on {location}"
        elif action['action'] == 'rotate':
            angle = action.get('angle', '90°')
            return f"Rotate {action['target']} by {angle}"
        else:
            return f"{action['action'].title()}: {action.get('target', 'N/A')}"
    
    def execute_visual_actions(self, actions):
        """Execute actions visually in Blender."""
        for i, action in enumerate(actions):
            try:
                if action['action'] == 'move_to':
                    self.create_or_move_object(action['target'], 'move', frame_offset=i*30)
                elif action['action'] == 'grab':
                    self.create_or_move_object(action['target'], 'grab', frame_offset=i*30)
                elif action['action'] == 'place':
                    self.create_or_move_object(action['target'], 'place', 
                                            action.get('location'), frame_offset=i*30)
                elif action['action'] == 'rotate':
                    self.rotate_object(action['target'], action.get('angle', 90), frame_offset=i*30)
            except Exception as e:
                print(f"Error executing action {action}: {e}")
    
    def create_or_move_object(self, object_name, action_type, location=None, frame_offset=0):
        """Create or move objects with animation."""
        try:
            # Clean object name
            obj_name = object_name.replace('the ', '').replace('a ', '').strip()
            obj = bpy.data.objects.get(obj_name)
            
            # Create object if it doesn't exist
            if obj is None:
                obj = self.create_object_by_name(obj_name)
            
            if obj is None:
                return
            
            # Set keyframes for animation
            start_frame = bpy.context.scene.frame_current + frame_offset
            end_frame = start_frame + 24  # 1 second at 24fps
            
            # Set initial keyframe
            bpy.context.scene.frame_set(start_frame)
            obj.keyframe_insert(data_path="location", index=-1)
            
            # Animate based on action
            bpy.context.scene.frame_set(end_frame)
            
            if action_type == 'move' or action_type == 'grab':
                obj.location.z += 0.5  # Lift object
            elif action_type == 'place' and location:
                self.move_to_location(obj, location)
            
            obj.keyframe_insert(data_path="location", index=-1)
            
        except Exception as e:
            print(f"Error in create_or_move_object: {e}")
    
    def create_object_by_name(self, name):
        """Create appropriate object based on name."""
        try:
            if 'cube' in name.lower():
                bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
            elif 'sphere' in name.lower():
                bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1))
            elif 'cylinder' in name.lower():
                bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 1))
            elif 'cone' in name.lower():
                bpy.ops.mesh.primitive_cone_add(location=(0, 0, 1))
            else:
                bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
            
            obj = bpy.context.active_object
            obj.name = name
            
            # Set color based on name
            self.set_object_color(obj, name)
            
            return obj
            
        except Exception as e:
            print(f"Error creating object: {e}")
            return None
    
    def set_object_color(self, obj, name):
        """Set object color based on name."""
        try:
            colors = {
                'red': (1, 0, 0, 1),
                'blue': (0, 0, 1, 1), 
                'green': (0, 1, 0, 1),
                'yellow': (1, 1, 0, 1),
                'purple': (1, 0, 1, 1),
                'orange': (1, 0.5, 0, 1),
                'white': (1, 1, 1, 1),
                'black': (0, 0, 0, 1)
            }
            
            color = (0.8, 0.8, 0.8, 1)  # Default gray
            for color_name, color_value in colors.items():
                if color_name in name.lower():
                    color = color_value
                    break
            
            # Create and assign material
            mat_name = f"{obj.name}_material"
            mat = bpy.data.materials.get(mat_name)
            
            if mat is None:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color
            
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
                
        except Exception as e:
            print(f"Error setting color: {e}")
    
    def move_to_location(self, obj, location_name):
        """Move object to named location."""
        locations = {
            'table': (2, 0, 1),
            'shelf': (-2, 0, 2),
            'corner': (3, 3, 0),
            'center': (0, 0, 1),
            'left': (-3, 0, 1),
            'right': (3, 0, 1),
            'front': (0, -3, 1),
            'back': (0, 3, 1)
        }
        
        for loc_name, coords in locations.items():
            if loc_name in location_name.lower():
                obj.location = coords
                return
        
        # Default movement
        obj.location.x += 2
    
    def rotate_object(self, object_name, angle, frame_offset=0):
        """Rotate object with animation."""
        try:
            obj_name = object_name.replace('the ', '').replace('a ', '').strip()
            obj = bpy.data.objects.get(obj_name)
            
            if obj is None:
                return
            
            start_frame = bpy.context.scene.frame_current + frame_offset
            end_frame = start_frame + 24
            
            # Set initial rotation keyframe
            bpy.context.scene.frame_set(start_frame)
            obj.keyframe_insert(data_path="rotation_euler", index=-1)
            
            # Apply rotation
            bpy.context.scene.frame_set(end_frame)
            import math
            obj.rotation_euler.z += math.radians(float(angle))
            obj.keyframe_insert(data_path="rotation_euler", index=-1)
            
        except Exception as e:
            print(f"Error rotating object: {e}")

class ROBOT_OT_quick_command(Operator):
    """Execute a predefined quick command."""
    bl_idname = "robot.quick_command"
    bl_label = "Quick Command"
    bl_description = "Execute a predefined command"
    
    command: StringProperty()
    
    def execute(self, context):
        context.scene.robot_nlp_pro.command = self.command
        bpy.ops.robot.execute_command()
        return {'FINISHED'}

class ROBOT_OT_preview_animation(Operator):
    """Preview the generated animation."""
    bl_idname = "robot.preview_animation"
    bl_label = "Preview Animation"
    bl_description = "Preview the robot animation sequence"
    
    def execute(self, context):
        scene = context.scene
        props = scene.robot_nlp_pro
        
        if props.last_animation_frames <= 0:
            self.report({'INFO'}, "No animation to preview. Execute a command first.")
            return {'FINISHED'}
        
        # Set animation range
        scene.frame_start = scene.frame_current
        scene.frame_end = scene.frame_current + props.last_animation_frames
        
        # Start playback
        if not scene.frame_current == scene.frame_start:
            scene.frame_set(scene.frame_start)
        
        # Set playback speed
        if props.preview_mode == 'SLOW':
            bpy.ops.screen.animation_play()
        elif props.preview_mode == 'NORMAL':
            bpy.ops.screen.animation_play()
        else:  # FAST
            bpy.ops.screen.animation_play()
        
        self.report({'INFO'}, f"Playing {props.last_animation_frames} frame animation")
        return {'FINISHED'}

class ROBOT_OT_create_keyframes(Operator):
    """Create keyframes for manual editing."""
    bl_idname = "robot.create_keyframes"
    bl_label = "Create Keyframes"
    bl_description = "Create keyframes for all animated objects"
    
    def execute(self, context):
        # Select all objects with keyframes
        keyframed_objects = []
        for obj in bpy.context.scene.objects:
            if obj.animation_data and obj.animation_data.action:
                keyframed_objects.append(obj)
        
        if not keyframed_objects:
            self.report({'INFO'}, "No animated objects found")
            return {'FINISHED'}
        
        # Select all keyframed objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in keyframed_objects:
            obj.select_set(True)
        
        if keyframed_objects:
            bpy.context.view_layer.objects.active = keyframed_objects[0]
        
        self.report({'INFO'}, f"Selected {len(keyframed_objects)} animated objects")
        return {'FINISHED'}

class ROBOT_OT_reset_settings(Operator):
    """Reset settings to defaults."""
    bl_idname = "robot.reset_settings"
    bl_label = "Reset Settings"
    bl_description = "Reset all settings to default values"
    
    def execute(self, context):
        props = context.scene.robot_nlp_pro
        props.confidence_threshold = 0.7
        props.animation_speed = 1.0
        props.safety_mode = True
        props.debug_mode = False
        props.use_voice_input = False
        props.auto_execute = False
        props.preview_mode = 'NORMAL'
        
        self.report({'INFO'}, "Settings reset to defaults")
        return {'FINISHED'}

class ROBOT_OT_open_settings(Operator):
    """Open settings panel."""
    bl_idname = "robot.open_settings"
    bl_label = "Settings"
    bl_description = "Open advanced settings"
    
    def execute(self, context):
        self.report({'INFO'}, "Check the Advanced Settings panel below")
        return {'FINISHED'}

class RobotNLPProProperties(PropertyGroup):
    """Enhanced properties for Robot NLP Pro."""
    
    # Command input
    command: StringProperty(
        name="Command",
        description="Natural language command for the robot",
        default="pick up the red cube and place it on the table"
    )
    
    # Settings
    confidence_threshold: FloatProperty(
        name="Confidence Threshold",
        description="Minimum confidence required to execute commands",
        default=0.7,
        min=0.0,
        max=1.0
    )
    
    animation_speed: FloatProperty(
        name="Animation Speed",
        description="Speed multiplier for animations",
        default=1.0,
        min=0.1,
        max=5.0
    )
    
    safety_mode: BoolProperty(
        name="Safety Mode",
        description="Block potentially unsafe commands",
        default=True
    )
    
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Show detailed debug information",
        default=False
    )
    
    use_voice_input: BoolProperty(
        name="Voice Input",
        description="Enable voice command input (future feature)",
        default=False
    )
    
    auto_execute: BoolProperty(
        name="Auto Execute",
        description="Automatically execute commands as you type",
        default=False
    )
    
    preview_mode: EnumProperty(
        name="Preview Mode",
        description="Animation preview speed",
        items=[
            ('SLOW', "Slow", "Slow motion preview"),
            ('NORMAL', "Normal", "Normal speed preview"),
            ('FAST', "Fast", "Fast preview")
        ],
        default='NORMAL'
    )
    
    # Results
    last_result: BoolProperty(default=False)
    last_success: BoolProperty(default=False)
    last_confidence: FloatProperty(default=0.0)
    last_intent: StringProperty(default="")
    last_actions: StringProperty(default="")
    last_animation_frames: IntProperty(default=0)

# Registration
classes = [
    RobotNLPProProperties,
    ROBOT_PT_main_panel,
    ROBOT_PT_command_panel,
    ROBOT_PT_animation_panel,
    ROBOT_PT_results_panel,
    ROBOT_PT_settings_panel,
    ROBOT_OT_execute_command,
    ROBOT_OT_quick_command,
    ROBOT_OT_preview_animation,
    ROBOT_OT_create_keyframes,
    ROBOT_OT_reset_settings,
    ROBOT_OT_open_settings,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.robot_nlp_pro = bpy.props.PointerProperty(type=RobotNLPProProperties)
    
    # Initialize NLP on startup
    initialize_nlp()
    print("🤖 Robot NLP Controller Pro - Loaded Successfully!")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.robot_nlp_pro

if __name__ == "__main__":
    register() 