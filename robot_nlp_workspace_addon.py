bl_info = {
    "name": "Robot NLP Workspace Pro",
    "author": "Robot Animator Plus Delux 3000",
    "version": (2, 5),
    "blender": (3, 0, 0),
    "location": "Robot NLP Workspace Tab",
    "description": "Complete Robot NLP Workspace with Custom Layout and Dedicated Interface",
    "category": "Workspace",
}

import bpy
import sys
import os
import json
import time
from bpy.types import Panel, Operator, PropertyGroup, WorkSpaceTool, Header, Menu
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
    if len(command_history) > 20:
        command_history = command_history[-20:]

# Custom Header for Robot NLP Workspace
class ROBOT_HT_header(Header):
    """Custom header for Robot NLP workspace."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    
    def draw(self, context):
        layout = self.layout
        
        # Robot NLP branding
        row = layout.row(align=True)
        row.label(text="🤖 ROBOT NLP WORKSPACE", icon='CON_ARMATURE')
        
        # AI Status
        if NLP_AVAILABLE and nlp_processor is not None:
            row.label(text="🟢 AI READY", icon='CHECKMARK')
        elif NLP_AVAILABLE:
            row.label(text="🟡 INITIALIZING", icon='TIME')
        else:
            row.label(text="🔴 AI OFFLINE", icon='ERROR')
        
        layout.separator_spacer()
        
        # Quick action buttons in header
        row = layout.row(align=True)
        row.scale_x = 1.2
        row.operator("robot.emergency_stop", text="⏹️ STOP", icon='SNAP_FACE')
        row.operator("robot.reset_scene", text="🔄 RESET", icon='FILE_REFRESH')
        row.operator("robot.save_animation", text="💾 SAVE", icon='FILE_TICK')

# Large Command Center Panel (takes up major screen space)
class ROBOT_PT_command_center(Panel):
    """Main command center panel - takes up large area."""
    bl_label = "🎯 ROBOT COMMAND CENTER"
    bl_idname = "ROBOT_PT_command_center"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_workspace
        
        # Make the panel much larger and more prominent
        layout.scale_y = 1.5
        
        # Large header
        header_box = layout.box()
        header_box.scale_y = 2
        header_row = header_box.row()
        header_row.alignment = 'CENTER'
        header_row.label(text="🚀 NATURAL LANGUAGE ROBOT CONTROL", icon='ARMATURE_DATA')
        
        layout.separator()
        
        # Giant command input area
        cmd_box = layout.box()
        cmd_box.label(text="💬 COMMAND INPUT:", icon='SYNTAX_ON')
        
        # Make text input much larger
        cmd_row = cmd_box.row()
        cmd_row.scale_y = 3
        cmd_row.prop(props, "command", text="")
        
        # Large execute button
        exec_row = cmd_box.row()
        exec_row.scale_y = 3
        if props.command.strip():
            exec_row.operator("robot.execute_command", text="🚀 EXECUTE ROBOT COMMAND", icon='PLAY')
        else:
            exec_row.enabled = False
            exec_row.operator("robot.execute_command", text="⚠️ ENTER COMMAND FIRST", icon='ERROR')
        
        layout.separator()
        
        # Large quick commands grid
        quick_box = layout.box()
        quick_box.label(text="⚡ QUICK ROBOT COMMANDS:", icon='PRESET')
        
        # Grid of large buttons
        grid = quick_box.grid_flow(row_major=True, columns=2, align=True)
        grid.scale_y = 2
        
        grid.operator("robot.quick_command", text="🔴 PICK RED CUBE", icon='MESH_CUBE').command = "pick up the red cube"
        grid.operator("robot.quick_command", text="🏠 ROBOT HOME", icon='HOME').command = "move robot to home position"
        grid.operator("robot.quick_command", text="🔵 GRAB SPHERE", icon='MESH_UVSPHERE').command = "grab the blue sphere"
        grid.operator("robot.quick_command", text="📦 PLACE ON TABLE", icon='MESH_PLANE').command = "place it on the table"
        grid.operator("robot.quick_command", text="🔄 ROTATE 90°", icon='FILE_REFRESH').command = "rotate the cylinder 90 degrees"
        grid.operator("robot.quick_command", text="🎨 ORGANIZE COLORS", icon='COLOR').command = "organize all objects by color"

# Large Status Monitor Panel
class ROBOT_PT_status_monitor(Panel):
    """Large status monitoring panel."""
    bl_label = "📊 ROBOT STATUS MONITOR"
    bl_idname = "ROBOT_PT_status_monitor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_workspace
        
        layout.scale_y = 1.3
        
        # System status
        status_box = layout.box()
        status_box.label(text="🖥️ SYSTEM STATUS:", icon='DESKTOP')
        
        col = status_box.column(align=True)
        col.scale_y = 1.5
        
        # AI Status with large indicators
        if NLP_AVAILABLE and nlp_processor is not None:
            col.label(text="🟢 AI SYSTEM: READY", icon='CHECKMARK')
        elif NLP_AVAILABLE:
            col.label(text="🟡 AI SYSTEM: INITIALIZING", icon='TIME')
        else:
            col.label(text="🔴 AI SYSTEM: OFFLINE", icon='ERROR')
        
        col.label(text=f"📈 Commands Processed: {len(command_history)}")
        
        if command_history:
            last_confidence = command_history[-1].get('confidence', 0.0)
            success_rate = sum(1 for cmd in command_history if cmd['success']) / len(command_history)
            col.label(text=f"🎯 Last Confidence: {last_confidence:.2f}")
            col.label(text=f"✅ Success Rate: {success_rate:.1%}")
        
        layout.separator()
        
        # Latest command results
        if props.last_result:
            results_box = layout.box()
            results_box.label(text="📋 LATEST COMMAND RESULTS:", icon='PRESET')
            
            # Large success/failure indicator
            result_row = results_box.row()
            result_row.scale_y = 2
            if props.last_success:
                result_row.label(text="✅ COMMAND SUCCESSFUL", icon='CHECKMARK')
            else:
                result_row.label(text="❌ COMMAND FAILED", icon='ERROR')
            
            # Confidence display with visual bar
            conf_box = results_box.box()
            conf_box.label(text=f"🎯 AI Confidence: {props.last_confidence:.3f}")
            
            # Visual confidence bar
            conf_row = conf_box.row()
            bar_width = int(props.last_confidence * 20)  # 20 char wide bar
            bar = "█" * bar_width + "░" * (20 - bar_width)
            conf_row.label(text=f"[{bar}]")
            
            if props.last_intent:
                results_box.label(text=f"🧠 Understood: {props.last_intent}")
            
            if props.last_actions:
                results_box.label(text="🤖 Generated Actions:")
                actions = props.last_actions.split('|')
                for i, action in enumerate(actions[:3], 1):
                    results_box.label(text=f"   {i}. {action}")

# Animation Control Panel
class ROBOT_PT_animation_control(Panel):
    """Large animation control panel."""
    bl_label = "🎬 ROBOT ANIMATION CONTROL"
    bl_idname = "ROBOT_PT_animation_control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_workspace
        
        layout.scale_y = 1.4
        
        # Animation controls
        anim_box = layout.box()
        anim_box.label(text="🎬 ANIMATION CONTROLS:", icon='PLAY')
        
        # Large control buttons
        controls_row = anim_box.row(align=True)
        controls_row.scale_y = 2.5
        controls_row.operator("robot.preview_animation", text="▶️ PLAY", icon='PLAY')
        controls_row.operator("robot.pause_animation", text="⏸️ PAUSE", icon='PAUSE')
        controls_row.operator("robot.stop_animation", text="⏹️ STOP", icon='SQUARE')
        
        # Animation settings
        settings_col = anim_box.column(align=True)
        settings_col.scale_y = 1.5
        settings_col.prop(props, "animation_speed", text="🏃 Speed")
        settings_col.prop(props, "preview_mode", text="👁️ Preview Mode")
        
        if props.last_animation_frames > 0:
            anim_box.separator()
            info_col = anim_box.column(align=True)
            info_col.label(text=f"📊 Duration: {props.last_animation_frames} frames")
            info_col.label(text=f"⏱️ Time: {props.last_animation_frames/24:.1f} seconds")

# Robot Settings Panel
class ROBOT_PT_robot_settings(Panel):
    """Large robot settings panel."""
    bl_label = "⚙️ ROBOT CONFIGURATION"
    bl_idname = "ROBOT_PT_robot_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.robot_nlp_workspace
        
        layout.scale_y = 1.3
        
        # AI Configuration
        ai_box = layout.box()
        ai_box.label(text="🧠 AI CONFIGURATION:", icon='SETTINGS')
        
        ai_col = ai_box.column(align=True)
        ai_col.scale_y = 1.4
        ai_col.prop(props, "confidence_threshold", text="🎯 Min Confidence", slider=True)
        ai_col.prop(props, "safety_mode", text="🛡️ Safety Mode", toggle=True)
        ai_col.prop(props, "debug_mode", text="🔍 Debug Output", toggle=True)
        
        # Robot behavior settings
        robot_box = layout.box()
        robot_box.label(text="🤖 ROBOT BEHAVIOR:", icon='ARMATURE_DATA')
        
        robot_col = robot_box.column(align=True)
        robot_col.scale_y = 1.4
        robot_col.prop(props, "movement_speed", text="🏃 Movement Speed", slider=True)
        robot_col.prop(props, "precision_mode", text="🎯 Precision Mode", toggle=True)
        robot_col.prop(props, "auto_save", text="💾 Auto Save", toggle=True)
        
        # Reset button
        layout.separator()
        reset_row = layout.row()
        reset_row.scale_y = 2
        reset_row.operator("robot.reset_all_settings", text="🔄 RESET ALL SETTINGS", icon='FILE_REFRESH')

# === OPERATORS ===
class ROBOT_OT_execute_command(Operator):
    """Execute the natural language command."""
    bl_idname = "robot.execute_command"
    bl_label = "Execute Robot Command"
    bl_description = "Process and execute the natural language robot command"
    
    def execute(self, context):
        scene = context.scene
        props = scene.robot_nlp_workspace
        command = props.command.strip()
        
        if not command:
            self.report({'WARNING'}, "⚠️ Please enter a robot command")
            return {'CANCELLED'}
        
        # Safety check
        if props.safety_mode and self.is_unsafe_command(command):
            self.report({'ERROR'}, "🛡️ Command blocked by safety mode")
            return {'CANCELLED'}
        
        if not NLP_AVAILABLE:
            self.report({'ERROR'}, "🔴 AI system not available")
            return {'CANCELLED'}
        
        if nlp_processor is None:
            if not initialize_nlp():
                self.report({'ERROR'}, "🔴 Failed to initialize AI system")
                return {'CANCELLED'}
        
        try:
            self.report({'INFO'}, f"🧠 Processing: {command}")
            result = nlp_processor.process_command(command)
            
            if result['confidence'] < props.confidence_threshold:
                self.report({'WARNING'}, f"🎯 Low confidence ({result['confidence']:.2f}). Adjust threshold or rephrase.")
                return {'CANCELLED'}
            
            # Store results
            props.last_result = True
            props.last_success = result['success']
            props.last_confidence = result['confidence']
            props.last_intent = result['parsed_command']['intent']
            
            log_command(command, result)
            
            if result['actions']:
                actions_text = []
                total_frames = 0
                
                for action in result['actions']:
                    action_desc = self.format_action(action)
                    actions_text.append(action_desc)
                    total_frames += 30
                
                props.last_actions = '|'.join(actions_text)
                props.last_animation_frames = total_frames
                
                self.execute_visual_actions(result['actions'])
                
                self.report({'INFO'}, f"✅ Executed {len(result['actions'])} robot actions | Confidence: {result['confidence']:.2f}")
                
            else:
                props.last_actions = "No robot actions generated"
                self.report({'WARNING'}, "⚠️ No executable robot actions found")
        
        except Exception as e:
            self.report({'ERROR'}, f"💥 Robot command error: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def is_unsafe_command(self, command):
        """Check if command contains unsafe keywords."""
        unsafe_keywords = ['fast', 'quickly', 'throw', 'slam', 'crash', 'hit', 'break', 'destroy']
        return any(keyword in command.lower() for keyword in unsafe_keywords)
    
    def format_action(self, action):
        """Format action for display."""
        if action['action'] == 'move_to':
            return f"Move robot to {action['target']}"
        elif action['action'] == 'grab':
            return f"Robot grab {action['target']}"
        elif action['action'] == 'place':
            location = action.get('location', 'location')
            return f"Robot place {action['target']} on {location}"
        elif action['action'] == 'rotate':
            angle = action.get('angle', '90°')
            return f"Robot rotate {action['target']} by {angle}"
        else:
            return f"Robot {action['action']}: {action.get('target', 'N/A')}"
    
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
                print(f"Robot action error {action}: {e}")
    
    def create_or_move_object(self, object_name, action_type, location=None, frame_offset=0):
        """Create or move objects with animation."""
        try:
            obj_name = object_name.replace('the ', '').replace('a ', '').strip()
            obj = bpy.data.objects.get(obj_name)
            
            if obj is None:
                obj = self.create_object_by_name(obj_name)
            
            if obj is None:
                return
            
            start_frame = bpy.context.scene.frame_current + frame_offset
            end_frame = start_frame + 24
            
            bpy.context.scene.frame_set(start_frame)
            obj.keyframe_insert(data_path="location", index=-1)
            
            bpy.context.scene.frame_set(end_frame)
            
            if action_type == 'move' or action_type == 'grab':
                obj.location.z += 0.5
            elif action_type == 'place' and location:
                self.move_to_location(obj, location)
            
            obj.keyframe_insert(data_path="location", index=-1)
            
        except Exception as e:
            print(f"Robot object manipulation error: {e}")
    
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
            self.set_object_color(obj, name)
            return obj
            
        except Exception as e:
            print(f"Robot object creation error: {e}")
            return None
    
    def set_object_color(self, obj, name):
        """Set object color based on name."""
        try:
            colors = {
                'red': (1, 0, 0, 1), 'blue': (0, 0, 1, 1), 'green': (0, 1, 0, 1),
                'yellow': (1, 1, 0, 1), 'purple': (1, 0, 1, 1), 'orange': (1, 0.5, 0, 1),
                'white': (1, 1, 1, 1), 'black': (0, 0, 0, 1)
            }
            
            color = (0.8, 0.8, 0.8, 1)
            for color_name, color_value in colors.items():
                if color_name in name.lower():
                    color = color_value
                    break
            
            mat_name = f"{obj.name}_robot_material"
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
            print(f"Robot material error: {e}")
    
    def move_to_location(self, obj, location_name):
        """Move object to named location."""
        locations = {
            'table': (2, 0, 1), 'shelf': (-2, 0, 2), 'corner': (3, 3, 0),
            'center': (0, 0, 1), 'left': (-3, 0, 1), 'right': (3, 0, 1),
            'front': (0, -3, 1), 'back': (0, 3, 1)
        }
        
        for loc_name, coords in locations.items():
            if loc_name in location_name.lower():
                obj.location = coords
                return
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
            
            bpy.context.scene.frame_set(start_frame)
            obj.keyframe_insert(data_path="rotation_euler", index=-1)
            
            bpy.context.scene.frame_set(end_frame)
            import math
            obj.rotation_euler.z += math.radians(float(angle))
            obj.keyframe_insert(data_path="rotation_euler", index=-1)
            
        except Exception as e:
            print(f"Robot rotation error: {e}")

class ROBOT_OT_quick_command(Operator):
    """Execute a predefined quick robot command."""
    bl_idname = "robot.quick_command"
    bl_label = "Quick Robot Command"
    bl_description = "Execute a predefined robot command"
    
    command: StringProperty()
    
    def execute(self, context):
        context.scene.robot_nlp_workspace.command = self.command
        bpy.ops.robot.execute_command()
        return {'FINISHED'}

class ROBOT_OT_emergency_stop(Operator):
    """Emergency stop all robot operations."""
    bl_idname = "robot.emergency_stop"
    bl_label = "Emergency Stop"
    bl_description = "Immediately stop all robot operations"
    
    def execute(self, context):
        # Stop animation playback
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel()
        
        self.report({'WARNING'}, "🚨 EMERGENCY STOP - All robot operations halted")
        return {'FINISHED'}

class ROBOT_OT_reset_scene(Operator):
    """Reset the robot scene."""
    bl_idname = "robot.reset_scene"
    bl_label = "Reset Robot Scene"
    bl_description = "Reset the scene for new robot operations"
    
    def execute(self, context):
        # Reset timeline
        bpy.context.scene.frame_set(1)
        
        # Clear command
        context.scene.robot_nlp_workspace.command = ""
        context.scene.robot_nlp_workspace.last_result = False
        
        self.report({'INFO'}, "🔄 Robot scene reset")
        return {'FINISHED'}

class ROBOT_OT_save_animation(Operator):
    """Save the current robot animation."""
    bl_idname = "robot.save_animation"
    bl_label = "Save Robot Animation"
    bl_description = "Save the current robot animation"
    
    def execute(self, context):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"robot_animation_{timestamp}.blend"
        
        try:
            bpy.ops.wm.save_as_mainfile(filepath=filename)
            self.report({'INFO'}, f"💾 Saved robot animation: {filename}")
        except Exception as e:
            self.report({'ERROR'}, f"💥 Save failed: {str(e)}")
        
        return {'FINISHED'}

class ROBOT_OT_preview_animation(Operator):
    """Preview the robot animation."""
    bl_idname = "robot.preview_animation"
    bl_label = "Preview Robot Animation"
    bl_description = "Play preview of the robot animation"
    
    def execute(self, context):
        scene = context.scene
        props = scene.robot_nlp_workspace
        
        if props.last_animation_frames <= 0:
            self.report({'INFO'}, "📽️ No robot animation to preview")
            return {'FINISHED'}
        
        scene.frame_start = scene.frame_current
        scene.frame_end = scene.frame_current + props.last_animation_frames
        
        if not scene.frame_current == scene.frame_start:
            scene.frame_set(scene.frame_start)
        
        bpy.ops.screen.animation_play()
        self.report({'INFO'}, f"▶️ Playing {props.last_animation_frames} frame robot animation")
        return {'FINISHED'}

class ROBOT_OT_pause_animation(Operator):
    """Pause the robot animation."""
    bl_idname = "robot.pause_animation"
    bl_label = "Pause Robot Animation"
    
    def execute(self, context):
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel()
            self.report({'INFO'}, "⏸️ Robot animation paused")
        return {'FINISHED'}

class ROBOT_OT_stop_animation(Operator):
    """Stop the robot animation."""
    bl_idname = "robot.stop_animation"
    bl_label = "Stop Robot Animation"
    
    def execute(self, context):
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(1)
        self.report({'INFO'}, "⏹️ Robot animation stopped")
        return {'FINISHED'}

class ROBOT_OT_reset_all_settings(Operator):
    """Reset all robot settings to defaults."""
    bl_idname = "robot.reset_all_settings"
    bl_label = "Reset All Robot Settings"
    
    def execute(self, context):
        props = context.scene.robot_nlp_workspace
        props.confidence_threshold = 0.7
        props.animation_speed = 1.0
        props.movement_speed = 1.0
        props.safety_mode = True
        props.debug_mode = False
        props.precision_mode = False
        props.auto_save = True
        props.preview_mode = 'NORMAL'
        
        self.report({'INFO'}, "🔄 All robot settings reset to defaults")
        return {'FINISHED'}

# Properties
class RobotNLPWorkspaceProperties(PropertyGroup):
    """Properties for Robot NLP Workspace."""
    
    # Command input
    command: StringProperty(
        name="Robot Command",
        description="Natural language command for the robot",
        default="pick up the red cube and place it on the table"
    )
    
    # AI Settings
    confidence_threshold: FloatProperty(
        name="Confidence Threshold",
        description="Minimum AI confidence required to execute robot commands",
        default=0.7, min=0.0, max=1.0
    )
    
    animation_speed: FloatProperty(
        name="Animation Speed",
        description="Robot animation speed multiplier",
        default=1.0, min=0.1, max=5.0
    )
    
    movement_speed: FloatProperty(
        name="Robot Movement Speed",
        description="Robot movement speed in the scene",
        default=1.0, min=0.1, max=3.0
    )
    
    safety_mode: BoolProperty(
        name="Safety Mode",
        description="Block potentially dangerous robot commands",
        default=True
    )
    
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Show detailed robot debug information",
        default=False
    )
    
    precision_mode: BoolProperty(
        name="Precision Mode",
        description="Enable high-precision robot movements",
        default=False
    )
    
    auto_save: BoolProperty(
        name="Auto Save",
        description="Automatically save robot animations",
        default=True
    )
    
    preview_mode: EnumProperty(
        name="Preview Mode",
        description="Robot animation preview speed",
        items=[
            ('SLOW', "Slow Motion", "Slow motion robot preview"),
            ('NORMAL', "Normal Speed", "Normal speed robot preview"),
            ('FAST', "Fast Preview", "Fast robot preview")
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

def create_robot_workspace():
    """Create the custom Robot NLP workspace."""
    try:
        # Create a new workspace
        workspace = bpy.data.workspaces.new("Robot NLP Pro")
        
        # Set up the workspace with custom layout
        # This would require more complex workspace setup
        # For now, we'll modify the existing workspace
        
        print("🤖 Robot NLP Pro workspace created!")
        return True
    except Exception as e:
        print(f"Workspace creation error: {e}")
        return False

# Registration
classes = [
    RobotNLPWorkspaceProperties,
    ROBOT_HT_header,
    ROBOT_PT_command_center,
    ROBOT_PT_status_monitor,
    ROBOT_PT_animation_control,
    ROBOT_PT_robot_settings,
    ROBOT_OT_execute_command,
    ROBOT_OT_quick_command,
    ROBOT_OT_emergency_stop,
    ROBOT_OT_reset_scene,
    ROBOT_OT_save_animation,
    ROBOT_OT_preview_animation,
    ROBOT_OT_pause_animation,
    ROBOT_OT_stop_animation,
    ROBOT_OT_reset_all_settings,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.robot_nlp_workspace = bpy.props.PointerProperty(type=RobotNLPWorkspaceProperties)
    
    # Initialize NLP and create workspace
    initialize_nlp()
    create_robot_workspace()
    
    print("🚀 Robot NLP Workspace Pro - Complete Interface Loaded!")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.robot_nlp_workspace

if __name__ == "__main__":
    register() 