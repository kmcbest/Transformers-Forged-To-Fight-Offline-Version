import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import numpy as np

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

arm = bpy.data.objects.get("Armature")
scale = 89.73

print("Sideswipe scaled bone positions in Blender space:")
for b in arm.data.bones:
    if any(k in b.name for k in ["Collar", "UpperArm", "LowerArm", "Hand_L", "Sword_L", "Thumb_0_L"]):
        h = arm.matrix_world @ b.head_local
        # X_b = h.x * scale, Y_b = -h.z * scale, Z_b = h.y * scale
        bx = h.x * scale
        by = -h.z * scale
        bz = h.y * scale
        print(f"  {b.name:20s}: Blender pos = ({bx:6.3f}, {by:6.3f}, {bz:6.3f})")
