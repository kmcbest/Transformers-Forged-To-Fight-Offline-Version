import bpy
import math
from pathlib import Path

BLEND_PATH = "tools/demolishor/demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

# Add side camera (looking from Right to Left, along X axis)
cam_data = bpy.data.cameras.new("SideCam")
cam_obj = bpy.data.objects.new("SideCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (15.0, 0.0, 6.0)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))

# Light
light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (10, -10, 15)
light_obj.rotation_euler = (math.radians(45), math.radians(30), math.radians(-45))
light_data.energy = 3.0

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800

# Render frame 0 (Rest Pose)
bpy.context.scene.frame_current = 0
bpy.context.scene.render.filepath = "tools/demolishor/side_frame_0.png"
bpy.ops.render.render(write_still=True)

# Render frame 10 (Stride peak)
bpy.context.scene.frame_current = 10
bpy.context.scene.render.filepath = "tools/demolishor/side_frame_10.png"
bpy.ops.render.render(write_still=True)

# Render frame 20 (Mid stride)
bpy.context.scene.frame_current = 20
bpy.context.scene.render.filepath = "tools/demolishor/side_frame_20.png"
bpy.ops.render.render(write_still=True)

print("[✓] Rendered side frames 0, 10, 20")
