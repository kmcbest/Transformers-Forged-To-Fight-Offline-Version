import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector, Matrix

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# First check in REST pose (Static Pose): where are the vertices of Wing_01, Wing_02, bird_Head, beak, beak_the bottom, bird_neck?
# Wait: in Rest Pose (Static Pose), ALL vertices of Swoop.001 are ALREADY 100% seamlessly connected!
# Look at 01_rest_sbs.png and 04_back_sbs.png:
# In Static Pose, Wing_01 and Wing_02 are connected at the wing hinge, and bird_Head + beak + beak_the bottom are connected on the chest!
# Why did they separate ONLY when `Bip001|vehicle_idle01|Base Layer` was applied in Blender?
# Let's check EVERY bone that has non-(1,1,1) scale or non-(0,0,0) location in `Bip001|vehicle_idle01|Base Layer`!

act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

print("=== Bones in vehicle_idle01 (frame 1) with non-zero pb.location or non-1 pb.scale ===")
for pb in arm.pose.bones:
    loc_len = pb.location.length
    scl_err = (pb.scale - Vector((1, 1, 1))).length
    if loc_len > 1e-3 or scl_err > 1e-3:
        print(f"  {pb.name:28s}: loc={tuple(round(x, 4) for x in pb.location)} | scale={tuple(round(x, 4) for x in pb.scale)} | rot_q={tuple(round(x, 4) for x in pb.rotation_quaternion)}")
