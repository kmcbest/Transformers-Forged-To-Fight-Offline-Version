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

# Slightly angled 3/4 view focusing on waist and legs
cam.location = (2.5, -8.0, 5.0)
cam.rotation_euler = (math.radians(82.0), 0, math.radians(18.0))

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1100
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

# Render at Frame 10 (running stride where leg is raised)
bpy.context.scene.frame_set(10)
out_png = ROOT / "tools" / "demolishor" / "preview_waist_fixed.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered waist fix preview to {out_png}")
