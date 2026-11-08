import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_prepared.fbx")

mesh = bpy.data.objects["cha_vortex_gs_00"]
for side, s_sign in [("L", -1.0), ("R", 1.0)]:
    vg_name = "LeftForeArm" if side == "L" else "RightForeArm"
    # The blade vertices are the last 2834 per side
    offset = 11706 if side == "L" else 11706 + 2834
    indices = list(range(offset, offset + 2834))
    
    # Wrist pivot: X = -2.571 (L) / +2.571 (R), Y = -0.049, Z = 5.746
    pivot = mathutils.Vector((s_sign * 2.571, -0.049, 5.746))
    
    # Scale by 0.68 around pivot, and rotate 12 deg forward around X
    rot_x = mathutils.Matrix.Rotation(math.radians(12.0), 4, 'X')
    scale_m = mathutils.Matrix.Diagonal((0.75, 0.75, 0.65, 1.0))
    
    T = mathutils.Matrix.Translation(pivot)
    T_inv = mathutils.Matrix.Translation(-pivot)
    M = T @ rot_x @ scale_m @ T_inv
    
    for i in indices:
        v = mesh.data.vertices[i]
        v.co = M @ v.co

zs = [mesh.data.vertices[i].co.z for i in range(11706, 17374)]
print(f"Adjusted Blade Z range: [{min(zs):.3f}, {max(zs):.3f}] (feet at Z=0.000!)")
