import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

out_img = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\strongarm_prowl_full_body.png")

# Move camera to Y = -26.0, Z = 4.65
cam_obj = bpy.data.objects["Cam"]
cam_obj.location = (0.0, -26.0, 4.65)
cam_obj.data.lens = 45 # focal length

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered full body to {out_img}")
