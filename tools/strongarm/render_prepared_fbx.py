import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
out_img = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\test_prepared_blender.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

# Setup camera & light for full body
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0, -14.0, 4.5)
cam_obj.rotation_euler = (1.5708, 0, 0) # 90 deg around X

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered prepared FBX to {out_img}")
