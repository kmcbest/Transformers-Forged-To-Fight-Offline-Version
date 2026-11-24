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

arm = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        arm = o
        break

print(f"Armature: {arm.name if arm else None}")
if arm:
    finger_bones = [b.name for b in arm.data.bones if 'finger' in b.name.lower() or 'hand' in b.name.lower()]
    print(f"Hand/Finger bones ({len(finger_bones)}):")
    for b in sorted(finger_bones):
        print(f"  {b}")
