import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

# Hide unwanted
for o in bpy.data.objects:
    if o.name in ["Shadow", "Swoop_Weapon", "Symbol_DC"]:
        o.hide_render = True

arm = bpy.data.objects.get("Bip001")
if arm:
    arm.animation_data_clear()
    arm.data.pose_position = 'REST'

bpy.context.view_layer.update()

# Set up camera
cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera looking at center of robot
# Y is front/back in Blender (-Y is front)
cam_obj.location = (0.0, -5.5, 0.0)
cam_obj.rotation_euler = (1.5708, 0, 0) # 90 deg around X
cam_data.lens = 50.0

# Add lights
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.8, -0.3, 0.6)

fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 1.5
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (0.8, 0.5, -2.5)

out_png = ROOT / "renders/swoop/swoop_static_pose_blender_render.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Static Pose to: {out_png}")
