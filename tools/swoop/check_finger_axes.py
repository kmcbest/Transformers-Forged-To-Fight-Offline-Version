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
for side in ["L", "R"]:
    for f in ["Finger0", "Finger1", "Finger2"]:
        b = arm.data.bones.get(f"Bone_{side}_{f}")
        print(f"Bone_{side}_{f}: matrix_local=\n{b.matrix_local}")
