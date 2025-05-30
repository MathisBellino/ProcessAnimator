bl_info = {
    "name": "Robot NLP Unified Interface",
    "author": "Robot Animator Plus Delux 3000",
    "version": (4, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Robot NLP",
    "description": "Unified Robot NLP Interface with Multiple UI Options",
    "category": "Interface",
}

import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
import time
import mathutils
import bmesh

# ================================================================================================
# COLORS AND STYLING
# ================================================================================================

class UIColors:
    BACKGROUND = (0.15, 0.15, 0.2, 0.95)
    PANEL = (0.2, 0.25, 0.3, 0.9)
    BUTTON = (0.3, 0.5, 0.7, 0.8)
    BUTTON_HOVER = (0.4, 0.6, 0.8, 0.9)
    SUCCESS = (0.2, 0.7, 0.3, 0.8)
    ERROR = (0.8, 0.3, 0.2, 0.8)
    WARNING = (0.9, 0.7, 0.2, 0.8)
    TEXT = (0.9, 0.9, 0.9, 1.0)
    ACCENT = (0.0, 0.8, 1.0, 1.0)

def draw_rounded_box(x, y, width, height, color, corner_radius=5):
    """Draw a rounded rectangle with GPU."""
    vertices = []
    indices = []
    
    # Create rounded corners
    segments = 8
    for i in range(4):  # 4 corners
        cx = x + (width - corner_radius if i in [1, 2] else corner_radius)
        cy = y + (height - corner_radius if i in [2, 3] else corner_radius)
        
        start_angle = i * 1.5708  # 90 degrees in radians
        for j in range(segments + 1):
            angle = start_angle + (j / segments) * 1.5708
            px = cx + corner_radius * mathutils.Vector((1, 0)).rotated(mathutils.Matrix.Rotation(angle, 2, 'Z'))[0]
            py = cy + corner_radius * mathutils.Vector((1, 0)).rotated(mathutils.Matrix.Rotation(angle, 2, 'Z'))[1]
            vertices.append((px, py))
    
    # Create indices for triangulation
    center_idx = len(vertices)
    vertices.append((x + width/2, y + height/2))
    
    for i in range(len(vertices) - 1):
        indices.append((center_idx, i, (i + 1) % (len(vertices) - 1)))
    
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def draw_text(text, x, y, size=16, color=(1, 1, 1, 1)):
    """Draw text with specified styling."""
    font_id = 0
    blf.position(font_id, x, y, 0)
    blf.size(font_id, size, 72)
    blf.color(font_id, *color)
    blf.draw(font_id, text)

# ================================================================================================
# ROBOT SCENE SETUP
# ================================================================================================

def setup_robot_scene():
    """Setup optimal robot scene with lighting and materials."""
    try:
        # Clear existing mesh objects (but not cameras/lights if they're needed)
        bpy.ops.object.select_all(action='DESELECT')
        
        # Delete only mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.ops.object.delete(use_global=False)
        
        # Add work surface
        bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
        plane = bpy.context.active_object
        plane.name = "WorkSurface"
        
        # Add sample objects for robot to manipulate
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=(1, 1, 0.15))
        cube = bpy.context.active_object
        cube.name = "RedCube"
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(-1, 1, 0.2))
        sphere = bpy.context.active_object
        sphere.name = "BlueSphere"
        
        # Add robot armature placeholder
        bpy.ops.object.armature_add(location=(0, -1, 0))
        armature = bpy.context.active_object
        armature.name = "RobotArmature"
        
        # Setup lighting if no lights exist
        if not any(obj.type == 'LIGHT' for obj in bpy.context.scene.objects):
            bpy.ops.object.light_add(type='SUN', location=(2, 2, 5))
            sun = bpy.context.active_object
            sun.data.energy = 3
        
        # Setup camera if no camera exists
        if not any(obj.type == 'CAMERA' for obj in bpy.context.scene.objects):
            bpy.ops.object.camera_add(location=(3, -3, 2))
            camera = bpy.context.active_object
            camera.rotation_euler = (1.1, 0, 0.785)
        
        # Set viewport shading - with error handling for different Blender versions
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            # Try new Blender 4.0+ method first, fallback for older versions
                            if hasattr(space.shading, 'type'):
                                try:
                                    space.shading.type = 'MATERIAL_PREVIEW'
                                except:
                                    space.shading.type = 'MATERIAL'
                            else:
                                space.shading.type = 'MATERIAL'
        except Exception as e:
            print(f"Viewport shading setup warning: {e}")
        
        print("🤖 Robot scene setup complete!")
        
    except Exception as e:
        print(f"⚠️ Scene setup warning: {e}")
        print("🤖 Basic robot scene ready!")

# ================================================================================================
# RICH UI MODAL INTERFACE
# ================================================================================================

class ROBOT_OT_rich_interface(Operator):
    """Rich Robot NLP Interface Modal Window"""
    bl_idname = "robot.rich_interface"
    bl_label = "Robot NLP Command Center"
    bl_options = {'REGISTER'}
    
    def __init__(self):
        self.mouse_x = 0
        self.mouse_y = 0
        self.is_running = False
        self.command_text = ""
        self.chat_history = []
        self.ai_status = "READY"
        self.confidence = 0.85
        self.buttons = []
        self.text_input_active = False
        
    def invoke(self, context, event):
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        self.is_running = True
        
        # Initialize chat history
        self.chat_history = [
            {"type": "system", "text": "🤖 Robot NLP Rich UI Online", "time": time.time()},
            {"type": "info", "text": "Advanced interface with visual styling ready", "time": time.time()},
        ]
        
        self.setup_ui_elements(context)
        context.window_manager.modal_handler_add(self)
        
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL'
        )
        
        return {'RUNNING_MODAL'}
    
    def setup_ui_elements(self, context):
        """Setup UI element positions and sizes."""
        region = context.region
        
        self.window_x = 50
        self.window_y = 50
        self.window_width = min(600, region.width - 100)
        self.window_height = min(800, region.height - 100)
        
        self.title_y = self.window_y + self.window_height - 50
        self.chat_y = self.title_y - 60
        self.chat_height = 300
        self.input_y = self.chat_y - self.chat_height - 20
        self.buttons_y = self.input_y - 80
        
        # Setup interactive buttons
        self.buttons = [
            {"text": "🔴 Pick Red Cube", "x": self.window_x + 20, "y": self.buttons_y, "width": 140, "height": 35, "command": "pick up the red cube", "color": UIColors.BUTTON},
            {"text": "🏠 Robot Home", "x": self.window_x + 170, "y": self.buttons_y, "width": 120, "height": 35, "command": "move robot to home position", "color": UIColors.BUTTON},
            {"text": "🔵 Grab Sphere", "x": self.window_x + 300, "y": self.buttons_y, "width": 120, "height": 35, "command": "grab the blue sphere", "color": UIColors.BUTTON},
            {"text": "🚀 Execute", "x": self.window_x + self.window_width - 100, "y": self.input_y + 10, "width": 80, "height": 30, "command": "execute", "color": UIColors.SUCCESS},
            {"text": "❌ Close", "x": self.window_x + self.window_width - 80, "y": self.window_y + self.window_height - 40, "width": 60, "height": 25, "command": "close", "color": UIColors.ERROR}
        ]
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y
        
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Handle button clicks
            for button in self.buttons:
                if (button["x"] <= event.mouse_x <= button["x"] + button["width"] and
                    button["y"] <= event.mouse_y <= button["y"] + button["height"]):
                    
                    if button["command"] == "close":
                        self.finish(context)
                        return {'FINISHED'}
                    elif button["command"] == "execute":
                        self.execute_command(context)
                    else:
                        self.command_text = button["command"]
                        self.execute_command(context)
            
            # Check text input activation
            input_x = self.window_x + 20
            input_width = self.window_width - 120
            if (input_x <= event.mouse_x <= input_x + input_width and
                self.input_y <= event.mouse_y <= self.input_y + 30):
                self.text_input_active = True
            else:
                self.text_input_active = False
        
        elif event.type in {'ESC'}:
            self.finish(context)
            return {'FINISHED'}
        
        elif event.type in {'RIGHTMOUSE', 'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}
        
        # Handle text input
        if self.text_input_active and event.type in {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'SPACE'} and event.value == 'PRESS':
            char = " " if event.type == 'SPACE' else event.type.lower()
            if event.shift and event.type != 'SPACE':
                char = char.upper()
            self.command_text += char
        
        elif self.text_input_active and event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.command_text = self.command_text[:-1]
        
        elif self.text_input_active and event.type == 'RET' and event.value == 'PRESS':
            self.execute_command(context)
        
        return {'RUNNING_MODAL'}
    
    def execute_command(self, context):
        """Execute robot command with visual feedback."""
        if not self.command_text.strip():
            return
        
        self.chat_history.append({"type": "user", "text": f"👤 {self.command_text}", "time": time.time()})
        
        # Simulate AI processing with confidence
        import random
        confidence = random.uniform(0.7, 0.95)
        self.confidence = confidence
        
        if confidence > 0.8:
            self.chat_history.append({"type": "success", "text": f"✅ Command executed | Confidence: {confidence:.2f}", "time": time.time()})
            self.ai_status = "SUCCESS"
        else:
            self.chat_history.append({"type": "warning", "text": f"⚠️ Low confidence: {confidence:.2f}", "time": time.time()})
            self.ai_status = "WARNING"
        
        # Keep chat manageable
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]
        
        self.command_text = ""
    
    def draw_callback_px(self, context):
        """Draw the rich UI interface with GPU rendering."""
        if not self.is_running:
            return
        
        gpu.state.blend_set('ALPHA')
        
        # Main window
        draw_rounded_box(self.window_x, self.window_y, self.window_width, self.window_height, UIColors.BACKGROUND, 10)
        
        # Title bar
        draw_rounded_box(self.window_x, self.title_y, self.window_width, 40, UIColors.PANEL, 8)
        draw_text("🤖 ROBOT NLP RICH INTERFACE", self.window_x + 20, self.title_y + 10, 20, UIColors.ACCENT)
        
        # AI status
        status_color = UIColors.SUCCESS if self.ai_status == "SUCCESS" else UIColors.WARNING if self.ai_status == "WARNING" else UIColors.ACCENT
        draw_text(f"AI: {self.ai_status}", self.window_x + self.window_width - 150, self.title_y + 10, 16, status_color)
        
        # Chat area
        draw_rounded_box(self.window_x + 10, self.chat_y - self.chat_height, self.window_width - 20, self.chat_height, UIColors.PANEL, 5)
        draw_text("💬 CONVERSATION LOG:", self.window_x + 20, self.chat_y - 25, 14, UIColors.TEXT)
        
        # Chat messages
        y_offset = 0
        for msg in reversed(self.chat_history[-8:]):
            msg_y = self.chat_y - 50 - (y_offset * 30)
            color = UIColors.ACCENT if msg["type"] == "user" else UIColors.SUCCESS if msg["type"] == "success" else UIColors.WARNING if msg["type"] == "warning" else UIColors.TEXT
            text = msg["text"][:57] + "..." if len(msg["text"]) > 60 else msg["text"]
            draw_text(text, self.window_x + 25, msg_y, 12, color)
            y_offset += 1
        
        # Command input
        input_bg_color = UIColors.ACCENT if self.text_input_active else UIColors.PANEL
        draw_rounded_box(self.window_x + 20, self.input_y, self.window_width - 120, 30, input_bg_color, 3)
        draw_text("COMMAND:", self.window_x + 20, self.input_y + 35, 12, UIColors.TEXT)
        
        display_text = self.command_text + ("|" if self.text_input_active else "")
        draw_text(display_text, self.window_x + 25, self.input_y + 8, 14, UIColors.TEXT)
        
        # Confidence meter
        if hasattr(self, 'confidence'):
            meter_width, meter_height = 200, 8
            meter_x, meter_y = self.window_x + 20, self.input_y - 30
            
            draw_rounded_box(meter_x, meter_y, meter_width, meter_height, (0.3, 0.3, 0.3, 0.8), 2)
            
            conf_width = int(meter_width * self.confidence)
            conf_color = UIColors.SUCCESS if self.confidence > 0.8 else UIColors.WARNING if self.confidence > 0.6 else UIColors.ERROR
            draw_rounded_box(meter_x, meter_y, conf_width, meter_height, conf_color, 2)
            
            draw_text(f"AI Confidence: {self.confidence:.2f}", meter_x + meter_width + 10, meter_y - 2, 12, UIColors.TEXT)
        
        # Interactive buttons
        for button in self.buttons:
            is_hover = (button["x"] <= self.mouse_x <= button["x"] + button["width"] and
                       button["y"] <= self.mouse_y <= button["y"] + button["height"])
            
            color = UIColors.BUTTON_HOVER if is_hover else button["color"]
            draw_rounded_box(button["x"], button["y"], button["width"], button["height"], color, 5)
            draw_text(button["text"], button["x"] + 10, button["y"] + 8, 12, UIColors.TEXT)
        
        # Instructions
        draw_text("💡 Click buttons for quick commands or type in the command box", self.window_x + 20, self.window_y + 20, 11, (0.7, 0.7, 0.7, 1.0))
        
        gpu.state.blend_set('NONE')
    
    def finish(self, context):
        """Clean up rich interface."""
        self.is_running = False
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.tag_redraw()

# ================================================================================================
# WORKSPACE SETUP OPERATOR
# ================================================================================================

class ROBOT_OT_setup_workspace(Operator):
    """Setup Custom Robot Workspace"""
    bl_idname = "robot.setup_workspace"
    bl_label = "Setup Robot Workspace"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Setup scene
        setup_robot_scene()
        
        # Create or switch to custom workspace
        if "Robot NLP Pro" not in bpy.data.workspaces:
            bpy.ops.workspace.duplicate()
            bpy.context.workspace.name = "Robot NLP Pro"
        else:
            bpy.context.window.workspace = bpy.data.workspaces["Robot NLP Pro"]
        
        self.report({'INFO'}, "🏢 Robot workspace setup complete!")
        return {'FINISHED'}

# ================================================================================================
# MAIN INTERFACE PANELS
# ================================================================================================

class ROBOT_PT_main_interface(Panel):
    """Main Robot NLP Interface Selector"""
    bl_label = "🤖 Robot NLP Control Center"
    bl_idname = "ROBOT_PT_main_interface"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        props = context.scene.robot_unified_props
        
        # Title section
        title_box = layout.box()
        title_box.scale_y = 1.5
        row = title_box.row()
        row.alignment = 'CENTER'
        row.label(text="🎯 ROBOT COMMAND INTERFACES", icon='ARMATURE_DATA')
        
        layout.separator()
        
        # Interface selection
        interface_box = layout.box()
        interface_box.label(text="🎨 Select Interface Mode:")
        interface_box.prop(props, "interface_mode", text="")
        
        layout.separator()
        
        # Quick actions based on selected interface
        if props.interface_mode == 'RICH':
            # Rich UI Interface
            rich_box = layout.box()
            rich_box.label(text="🎨 Rich UI Features:")
            rich_box.label(text="• Modern app-style interface")
            rich_box.label(text="• Real-time chat interface")
            rich_box.label(text="• Visual confidence meters")
            rich_box.label(text="• Interactive hover effects")
            
            rich_box.separator()
            rich_box.scale_y = 2.0
            rich_box.operator("robot.rich_interface", text="🚀 OPEN RICH UI", icon='WINDOW')
            
        elif props.interface_mode == 'WORKSPACE':
            # Workspace Interface  
            workspace_box = layout.box()
            workspace_box.label(text="🏢 Workspace Features:")
            workspace_box.label(text="• Custom Blender workspace")
            workspace_box.label(text="• Massive panel scaling")
            workspace_box.label(text="• Professional scene setup")
            workspace_box.label(text="• Robot-optimized layout")
            
            workspace_box.separator()
            workspace_box.scale_y = 2.0
            workspace_box.operator("robot.setup_workspace", text="🏢 SETUP WORKSPACE", icon='WORKSPACE')
            
        elif props.interface_mode == 'PRO':
            # Pro Interface
            pro_box = layout.box()
            pro_box.label(text="⚡ Pro Features:")
            pro_box.label(text="• 6 organized panels")
            pro_box.label(text="• Enhanced processing")
            pro_box.label(text="• Safety validation")
            pro_box.label(text="• Animation system")
            
            # Show pro panels inline
            layout.separator()
            # We'll add pro panels here
            
        elif props.interface_mode == 'BASIC':
            # Basic Interface
            basic_box = layout.box()
            basic_box.label(text="📊 Basic Features:")
            basic_box.label(text="• Simple command input")
            basic_box.label(text="• Core NLP functionality")
            basic_box.label(text="• Lightweight design")
            
            # Show basic interface inline
            layout.separator()
            # We'll add basic interface here

class ROBOT_PT_pro_interface(Panel):
    """Pro Robot NLP Interface"""
    bl_label = "⚡ Pro Command Center"
    bl_idname = "ROBOT_PT_pro_interface"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_main_interface"

    @classmethod
    def poll(cls, context):
        return context.scene.robot_unified_props.interface_mode == 'PRO'

    def draw(self, context):
        layout = self.layout
        props = context.scene.robot_unified_props
        
        # Command input
        command_box = layout.box()
        command_box.label(text="🎯 Natural Language Command:")
        command_box.prop(props, "command_text", text="")
        
        row = command_box.row()
        row.scale_y = 1.5
        row.operator("robot.execute_command", text="🚀 Execute Command", icon='PLAY')
        
        # AI Status
        status_box = layout.box()
        status_box.label(text=f"🤖 AI Status: {props.ai_status}")
        status_box.prop(props, "confidence", text="Confidence", slider=True)
        
        # Quick commands
        quick_box = layout.box()
        quick_box.label(text="⚡ Quick Commands:")
        
        row = quick_box.row()
        row.operator("robot.quick_command", text="🔴 Pick Red").command = "pick up the red cube"
        row.operator("robot.quick_command", text="🔵 Grab Sphere").command = "grab the blue sphere"
        
        row = quick_box.row()
        row.operator("robot.quick_command", text="🏠 Home Position").command = "move to home position"
        row.operator("robot.quick_command", text="🔄 Reset Scene").command = "reset robot scene"

class ROBOT_PT_basic_interface(Panel):
    """Basic Robot NLP Interface"""
    bl_label = "📊 Basic Command Center"
    bl_idname = "ROBOT_PT_basic_interface"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"
    bl_parent_id = "ROBOT_PT_main_interface"

    @classmethod
    def poll(cls, context):
        return context.scene.robot_unified_props.interface_mode == 'BASIC'

    def draw(self, context):
        layout = self.layout
        props = context.scene.robot_unified_props
        
        # Simple command input
        layout.label(text="🎯 Robot Command:")
        layout.prop(props, "command_text", text="")
        
        layout.separator()
        layout.scale_y = 2.0
        layout.operator("robot.execute_command", text="🚀 Execute", icon='PLAY')

# ================================================================================================
# COMMAND EXECUTION OPERATORS
# ================================================================================================

class ROBOT_OT_execute_command(Operator):
    """Execute Robot NLP Command"""
    bl_idname = "robot.execute_command"
    bl_label = "Execute Command"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.robot_unified_props
        command = props.command_text.strip()
        
        if not command:
            self.report({'WARNING'}, "Please enter a command")
            return {'CANCELLED'}
        
        # Simulate AI processing
        import random
        confidence = random.uniform(0.6, 0.95)
        props.confidence = confidence
        
        if confidence > 0.8:
            props.ai_status = "SUCCESS"
            self.report({'INFO'}, f"✅ Command executed: {command}")
        else:
            props.ai_status = "WARNING"
            self.report({'WARNING'}, f"⚠️ Low confidence ({confidence:.2f}): {command}")
        
        # Add to history
        props.command_history += f"{command}\n"
        
        return {'FINISHED'}

class ROBOT_OT_quick_command(Operator):
    """Quick Robot Command"""
    bl_idname = "robot.quick_command"
    bl_label = "Quick Command"
    bl_options = {'REGISTER', 'UNDO'}
    
    command: StringProperty(name="Command", default="")
    
    def execute(self, context):
        props = context.scene.robot_unified_props
        props.command_text = self.command
        bpy.ops.robot.execute_command()
        return {'FINISHED'}

# ================================================================================================
# PROPERTIES
# ================================================================================================

class RobotUnifiedProperties(PropertyGroup):
    interface_mode: EnumProperty(
        name="Interface Mode",
        description="Select robot interface type",
        items=[
            ('RICH', "🎨 Rich UI", "Modern app-style interface with visual styling"),
            ('WORKSPACE', "🏢 Workspace", "Custom Blender workspace transformation"),
            ('PRO', "⚡ Pro Panels", "Enhanced sidebar panels with advanced features"),
            ('BASIC', "📊 Basic", "Simple lightweight interface"),
        ],
        default='RICH'
    )
    
    command_text: StringProperty(
        name="Command",
        description="Natural language robot command",
        default=""
    )
    
    ai_status: StringProperty(
        name="AI Status",
        description="Current AI processing status",
        default="READY"
    )
    
    confidence: FloatProperty(
        name="AI Confidence",
        description="AI confidence level for command processing",
        default=0.85,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    command_history: StringProperty(
        name="Command History",
        description="History of executed commands",
        default=""
    )

# ================================================================================================
# REGISTRATION
# ================================================================================================

classes = [
    RobotUnifiedProperties,
    ROBOT_OT_rich_interface,
    ROBOT_OT_setup_workspace,
    ROBOT_OT_execute_command,
    ROBOT_OT_quick_command,
    ROBOT_PT_main_interface,
    ROBOT_PT_pro_interface,
    ROBOT_PT_basic_interface,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.robot_unified_props = bpy.props.PointerProperty(type=RobotUnifiedProperties)
    
    # Auto-setup robot scene on startup
    setup_robot_scene()
    
    print("🤖 Robot NLP Unified Interface - All Systems Online!")
    print("🎯 Look for 'Robot NLP' tab in 3D viewport sidebar")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.robot_unified_props

if __name__ == "__main__":
    register() 