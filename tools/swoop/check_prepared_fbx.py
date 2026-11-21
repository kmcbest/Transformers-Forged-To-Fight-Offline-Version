import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
head_bone = arm.pose.bones.get("Head")
neck_bone = arm.pose.bones.get("Neck")
spine1_bone = arm.pose.bones.get("Spine1")
print(f"Head: {arm.matrix_world @ head_bone.head}")
print(f"Neck: {arm.matrix_world @ neck_bone.head}")
print(f"Spine1: {arm.matrix_world @ spine1_bone.head}")
