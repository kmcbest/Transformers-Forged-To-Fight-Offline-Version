import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
import math

ROOT = Path("E:/Agent/TFTF-blender")
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = ROOT / "3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# Let's inspect the positions of the vertices belonging to Bip001 L Finger1, Finger11, Finger12
# and the knuckle positions
for fi in range(5):
    for seg in ["", "1", "2"]:
        bname = f"Bip001 L Finger{fi}{seg}"
        b = arm_obj.data.bones.get(bname)
        if b:
            # Get bone local axes in armature space
            b_dir = (b.tail - b.head).normalized()
            mat = b.matrix_local.to_3x3()
            x_axis = mat @ Vector((1, 0, 0))
            y_axis = mat @ Vector((0, 1, 0))
            z_axis = mat @ Vector((0, 0, 1))
            print(f"{bname}: head={b.head}, length={b.length:.4f}")
            print(f"   local X in arm space: {x_axis}")
            print(f"   local Y in arm space: {y_axis}")
            print(f"   local Z in arm space: {z_axis}")
            break
