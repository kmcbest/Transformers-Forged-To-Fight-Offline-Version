import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix, Quaternion
import math

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = "E:/Agent/TFTF-blender/3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_obj = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm_obj = obj
        break

print(f"Found armature: {arm_obj.name}")

# Print bone axes for L and R fingers
for side in ["L", "R"]:
    for fi in range(5):
        bname = f"Bip001 {side} Finger{fi}"
        b = arm_obj.data.bones.get(bname)
        if b:
            # Check local X, Y, Z in armature space
            mat = b.matrix_local
            print(f"Bone {bname}: head={b.head}, tail={b.tail}, length={b.length:.4f}")
            print(f"  matrix_local 3x3 rows:")
            for row in mat.to_3x3():
                print(f"    ({row[0]:.3f}, {row[1]:.3f}, {row[2]:.3f})")
