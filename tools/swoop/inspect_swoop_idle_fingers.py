import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act:
    arm.animation_data_create()
    arm.animation_data.action = act
    bpy.context.scene.frame_set(0)
    print("Action Bip001|idle01|Base Layer applied at frame 0:")
    for pb in arm.pose.bones:
        if "Finger" in pb.name or "Hand" in pb.name:
            print(f"  {pb.name}: rot_euler={pb.rotation_euler}, rot_quat={pb.rotation_quaternion}, loc={pb.location}")
