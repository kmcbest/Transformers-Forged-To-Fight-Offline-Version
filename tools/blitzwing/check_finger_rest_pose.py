import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC))

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
bones = arm.data.bones

for fname in ["Bip001 L Hand", "Bip001 L Finger0", "Bip001 L Finger01", "Bip001 L Finger02",
              "Bip001 L Finger1", "Bip001 L Finger11", "Bip001 L Finger12",
              "Bip001 L Finger2", "Bip001 L Finger21", "Bip001 L Finger22"]:
    b = bones[fname]
    print(f"{fname}: head={b.head_local}, tail={b.tail_local}, len={(b.tail_local - b.head_local).length:.4f}")
