# -*- coding: utf-8 -*-
import bpy
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"
OUT_IMG = ROOT / "tools" / "demolishor" / "preview_plan_a.png"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Add camera looking at front of robot
cam_data = bpy.data.cameras.new("FrontPreviewCam")
cam_obj = bpy.data.objects.new("FrontPreviewCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera at +Y looking toward -Y (origin at Z=5.2)
cam_obj.location = (0, 16.0, 5.2)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(180))

# Sun light
light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (5, 10, 12)
light_obj.rotation_euler = (math.radians(-45), math.radians(20), math.radians(120))
light_data.energy = 3.5

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1000
bpy.context.scene.render.filepath = str(OUT_IMG)

bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Plan A preview to: {OUT_IMG}")
