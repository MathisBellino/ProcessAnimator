bl_info = {
    "name": "Robot NLP Rich UI",
    "author": "Robot Animator Plus Delux 3000",
    "version": (3, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Robot NLP",
    "description": "Rich UI Robot NLP Interface with Modern Styling",
    "category": "Interface",
}

import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty
import time
import mathutils

# Colors for rich UI
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
    
    # Create rounded corners with multiple points
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

class ROBOT_OT_rich_interface(Operator):
    """Open Rich Robot NLP Interface"""
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
        # Store initial mouse position
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        self.is_running = True
        
        # Add sample chat history
        self.chat_history = [
            {"type": "system", "text": "🤖 Robot NLP System Online", "time": time.time()},
            {"type": "info", "text": "Ready to receive natural language commands", "time": time.time()},
        ]
        
        # Define button areas
        self.setup_ui_elements(context)
        
        # Add modal handler
        context.window_manager.modal_handler_add(self)
        
        # Set up drawing
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL'
        )
        
        return {'RUNNING_MODAL'}
    
    def setup_ui_elements(self, context):
        """Setup UI element positions and sizes."""
        area = context.area
        region = context.region
        
        # Main window dimensions
        self.window_x = 50
        self.window_y = 50
        self.window_width = min(600, region.width - 100)
        self.window_height = min(800, region.height - 100)
        
        # UI element positions
        self.title_y = self.window_y + self.window_height - 50
        self.chat_y = self.title_y - 60
        self.chat_height = 300
        self.input_y = self.chat_y - self.chat_height - 20
        self.buttons_y = self.input_y - 80
        
        # Setup buttons
        self.buttons = [
            {
                "text": "🔴 Pick Red Cube",
                "x": self.window_x + 20,
                "y": self.buttons_y,
                "width": 140,
                "height": 35,
                "command": "pick up the red cube",
                "color": UIColors.BUTTON
            },
            {
                "text": "🏠 Robot Home",
                "x": self.window_x + 170,
                "y": self.buttons_y,
                "width": 120,
                "height": 35,
                "command": "move robot to home position",
                "color": UIColors.BUTTON
            },
            {
                "text": "🔵 Grab Sphere",
                "x": self.window_x + 300,
                "y": self.buttons_y,
                "width": 120,
                "height": 35,
                "command": "grab the blue sphere",
                "color": UIColors.BUTTON
            },
            {
                "text": "🚀 Execute",
                "x": self.window_x + self.window_width - 100,
                "y": self.input_y + 10,
                "width": 80,
                "height": 30,
                "command": "execute",
                "color": UIColors.SUCCESS
            },
            {
                "text": "❌ Close",
                "x": self.window_x + self.window_width - 80,
                "y": self.window_y + self.window_height - 40,
                "width": 60,
                "height": 25,
                "command": "close",
                "color": UIColors.ERROR
            }
        ]
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y
        
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Check button clicks
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
            
            # Check text input click
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
            if event.type == 'SPACE':
                self.command_text += " "
            else:
                char = event.type.lower()
                if event.shift:
                    char = char.upper()
                self.command_text += char
        
        elif self.text_input_active and event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.command_text = self.command_text[:-1]
        
        elif self.text_input_active and event.type == 'RET' and event.value == 'PRESS':
            self.execute_command(context)
        
        return {'RUNNING_MODAL'}
    
    def execute_command(self, context):
        """Execute the robot command."""
        if not self.command_text.strip():
            return
        
        # Add to chat history
        self.chat_history.append({
            "type": "user",
            "text": f"👤 {self.command_text}",
            "time": time.time()
        })
        
        # Simulate AI processing
        import random
        confidence = random.uniform(0.7, 0.95)
        self.confidence = confidence
        
        if confidence > 0.8:
            self.chat_history.append({
                "type": "success",
                "text": f"✅ Command executed | Confidence: {confidence:.2f}",
                "time": time.time()
            })
            self.ai_status = "SUCCESS"
        else:
            self.chat_history.append({
                "type": "warning",
                "text": f"⚠️ Low confidence: {confidence:.2f} | Command may be unclear",
                "time": time.time()
            })
            self.ai_status = "WARNING"
        
        # Keep chat history manageable
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]
        
        # Clear command
        self.command_text = ""
    
    def draw_callback_px(self, context):
        """Draw the rich UI interface."""
        if not self.is_running:
            return
        
        # Enable blending for transparency
        gpu.state.blend_set('ALPHA')
        
        # Draw main window background
        draw_rounded_box(
            self.window_x, self.window_y,
            self.window_width, self.window_height,
            UIColors.BACKGROUND, 10
        )
        
        # Draw title bar
        draw_rounded_box(
            self.window_x, self.title_y,
            self.window_width, 40,
            UIColors.PANEL, 8
        )
        
        # Draw title text
        draw_text(
            "🤖 ROBOT NLP COMMAND CENTER",
            self.window_x + 20, self.title_y + 10,
            20, UIColors.ACCENT
        )
        
        # Draw AI status
        status_color = UIColors.SUCCESS if self.ai_status == "SUCCESS" else UIColors.WARNING if self.ai_status == "WARNING" else UIColors.ACCENT
        draw_text(
            f"AI: {self.ai_status}",
            self.window_x + self.window_width - 150, self.title_y + 10,
            16, status_color
        )
        
        # Draw chat area background
        draw_rounded_box(
            self.window_x + 10, self.chat_y - self.chat_height,
            self.window_width - 20, self.chat_height,
            UIColors.PANEL, 5
        )
        
        # Draw chat history
        draw_text(
            "💬 CONVERSATION LOG:",
            self.window_x + 20, self.chat_y - 25,
            14, UIColors.TEXT
        )
        
        y_offset = 0
        for i, msg in enumerate(reversed(self.chat_history[-8:])):  # Show last 8 messages
            msg_y = self.chat_y - 50 - (y_offset * 30)
            
            if msg["type"] == "user":
                color = UIColors.ACCENT
            elif msg["type"] == "success":
                color = UIColors.SUCCESS
            elif msg["type"] == "warning":
                color = UIColors.WARNING
            elif msg["type"] == "error":
                color = UIColors.ERROR
            else:
                color = UIColors.TEXT
            
            # Truncate long messages
            text = msg["text"]
            if len(text) > 60:
                text = text[:57] + "..."
            
            draw_text(text, self.window_x + 25, msg_y, 12, color)
            y_offset += 1
        
        # Draw command input area
        input_bg_color = UIColors.ACCENT if self.text_input_active else UIColors.PANEL
        draw_rounded_box(
            self.window_x + 20, self.input_y,
            self.window_width - 120, 30,
            input_bg_color, 3
        )
        
        # Draw input label
        draw_text(
            "COMMAND:",
            self.window_x + 20, self.input_y + 35,
            12, UIColors.TEXT
        )
        
        # Draw command text
        display_text = self.command_text
        if self.text_input_active:
            display_text += "|"  # Cursor
        
        draw_text(
            display_text,
            self.window_x + 25, self.input_y + 8,
            14, UIColors.TEXT
        )
        
        # Draw confidence meter
        if hasattr(self, 'confidence'):
            meter_width = 200
            meter_height = 8
            meter_x = self.window_x + 20
            meter_y = self.input_y - 30
            
            # Background
            draw_rounded_box(meter_x, meter_y, meter_width, meter_height, (0.3, 0.3, 0.3, 0.8), 2)
            
            # Confidence bar
            conf_width = int(meter_width * self.confidence)
            conf_color = UIColors.SUCCESS if self.confidence > 0.8 else UIColors.WARNING if self.confidence > 0.6 else UIColors.ERROR
            draw_rounded_box(meter_x, meter_y, conf_width, meter_height, conf_color, 2)
            
            # Confidence text
            draw_text(
                f"AI Confidence: {self.confidence:.2f}",
                meter_x + meter_width + 10, meter_y - 2,
                12, UIColors.TEXT
            )
        
        # Draw buttons
        for button in self.buttons:
            # Check if mouse is hovering
            is_hover = (button["x"] <= self.mouse_x <= button["x"] + button["width"] and
                       button["y"] <= self.mouse_y <= button["y"] + button["height"])
            
            color = UIColors.BUTTON_HOVER if is_hover else button["color"]
            
            draw_rounded_box(
                button["x"], button["y"],
                button["width"], button["height"],
                color, 5
            )
            
            # Button text
            text_x = button["x"] + 10
            text_y = button["y"] + 8
            draw_text(button["text"], text_x, text_y, 12, UIColors.TEXT)
        
        # Draw instructions
        draw_text(
            "💡 Click buttons for quick commands or type in the command box",
            self.window_x + 20, self.window_y + 20,
            11, (0.7, 0.7, 0.7, 1.0)
        )
        
        gpu.state.blend_set('NONE')
    
    def finish(self, context):
        """Clean up and finish the operator."""
        self.is_running = False
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.tag_redraw()

class ROBOT_PT_rich_launcher(Panel):
    """Panel to launch the rich interface."""
    bl_label = "🚀 Robot NLP Rich UI"
    bl_idname = "ROBOT_PT_rich_launcher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot NLP"

    def draw(self, context):
        layout = self.layout
        
        # Make the launch button large and prominent
        layout.scale_y = 2.0
        
        # Title
        title_box = layout.box()
        title_box.scale_y = 1.5
        row = title_box.row()
        row.alignment = 'CENTER'
        row.label(text="🎯 ROBOT COMMAND CENTER", icon='ARMATURE_DATA')
        
        layout.separator()
        
        # Launch button
        launch_box = layout.box()
        launch_box.scale_y = 3.0
        launch_row = launch_box.row()
        launch_row.alignment = 'CENTER'
        launch_row.operator("robot.rich_interface", text="🚀 OPEN RICH UI", icon='WINDOW')
        
        layout.separator()
        
        # Info
        info_box = layout.box()
        info_box.label(text="✨ Features:")
        info_box.label(text="• Modern app-style interface")
        info_box.label(text="• Real-time chat interface")
        info_box.label(text="• Visual confidence meters")
        info_box.label(text="• Styled buttons and panels")
        info_box.label(text="• Interactive command input")

# Properties for storing state
class RobotRichUIProperties(PropertyGroup):
    last_command: StringProperty(
        name="Last Command",
        description="Last executed robot command",
        default=""
    )
    
    ui_scale: FloatProperty(
        name="UI Scale",
        description="Scale factor for the rich UI",
        default=1.0,
        min=0.5,
        max=2.0
    )

# Registration
classes = [
    RobotRichUIProperties,
    ROBOT_OT_rich_interface,
    ROBOT_PT_rich_launcher,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.robot_rich_ui = bpy.props.PointerProperty(type=RobotRichUIProperties)
    print("🎨 Robot NLP Rich UI - Modern Interface Loaded!")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.robot_rich_ui

if __name__ == "__main__":
    register() 