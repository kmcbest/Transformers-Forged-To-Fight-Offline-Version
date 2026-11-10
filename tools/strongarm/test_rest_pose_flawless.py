import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
out_img = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\strongarm_rest_pose_flawless.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
# Set to REST position!
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0.0, -0.45, 0.105)
cam_obj.rotation_euler = (1.5707963, 0.0, 0.0)

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.5, 0.3, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered flawless rest pose to {out_img}")
