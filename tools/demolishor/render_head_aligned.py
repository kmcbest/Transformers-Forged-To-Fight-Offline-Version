# -*- coding: utf-8 -*-
import bpy
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "tools" / "demolishor" / "demolishor_phase2_inspect.blend"))

cam = bpy.data.objects.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if cam.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Match user's 3/4 angle (slightly from right and front looking up at head)
cam.location = (1.8, -3.2, 9.4)
cam.rotation_euler = (math.radians(85.0), 0, math.radians(28.0))

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

out_png = ROOT / "tools" / "demolishor" / "preview_head_aligned.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered head alignment preview to {out_png}")
