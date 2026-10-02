import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("SK_CH_11")
mesh = bpy.data.objects.get("SK_CH_11.001")

for o in list(bpy.context.scene.collection.objects):
    if o.name not in ["SK_CH_11", "SK_CH_11.001"]:
        bpy.data.objects.remove(o, do_unlink=True)

# Test curling left hand fingers:
# In local bone space, rotation around X or Z:
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# Let's inspect bone matrix_local of l_index_01_skin
b_ind = arm.data.bones.get("l_index_01_skin")
print(f"Index matrix local:\n{b_ind.matrix_local}")

# Let's try curling 4 fingers: Index, Middle, Ring, Pinky
# 70 degrees around local X:
rot_curl_01 = mathutils.Euler((0.0, 0.0, math.radians(70.0))).to_quaternion()
rot_curl_02 = mathutils.Euler((0.0, 0.0, math.radians(75.0))).to_quaternion()
rot_curl_03 = mathutils.Euler((0.0, 0.0, math.radians(60.0))).to_quaternion()

for f_base in ["l_index", "l_middle", "l_ring", "l_pinky"]:
    pb1 = arm.pose.bones.get(f"{f_base}_01_skin")
    pb2 = arm.pose.bones.get(f"{f_base}_02_skin")
    pb3 = arm.pose.bones.get(f"{f_base}_03_skin")
    if pb1: pb1.rotation_quaternion = rot_curl_01
    if pb2: pb2.rotation_quaternion = rot_curl_02
    if pb3: pb3.rotation_quaternion = rot_curl_03

# Thumb curled across palm
pb_t1 = arm.pose.bones.get("l_thumb_01_skin")
pb_t2 = arm.pose.bones.get("l_thumb_02_skin")
pb_t3 = arm.pose.bones.get("l_thumb_03_skin")
if pb_t1:
    pb_t1.rotation_quaternion = mathutils.Euler((math.radians(20.0), math.radians(35.0), math.radians(-30.0))).to_quaternion()
if pb_t2:
    pb_t2.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(-60.0))).to_quaternion()
if pb_t3:
    pb_t3.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(-40.0))).to_quaternion()

bpy.context.view_layer.update()

# Setup camera close to left hand:
# Left hand is around (0.0, 1.86, 4.63)
cam_data = bpy.data.cameras.new("HandCam")
cam_obj = bpy.data.objects.new("HandCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (2.5, 2.0, 4.5)
cam_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

light = bpy.data.lights.new(name="Sun", type='SUN')
light.energy = 5.0
l_obj = bpy.data.objects.new("Sun", light)
bpy.context.scene.collection.objects.link(l_obj)
l_obj.rotation_euler = (math.radians(45.0), math.radians(45.0), 0.0)

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800

bpy.context.scene.render.filepath = str(OUT_DIR / "test_fist_curl_X.png")
bpy.ops.render.render(write_still=True)
print("[✓] Rendered test_fist_curl_X.png")
