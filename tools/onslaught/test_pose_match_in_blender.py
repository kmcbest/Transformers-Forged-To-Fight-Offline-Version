import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
import mathutils

MASTER_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))

ons_arm = bpy.data.objects["Onslaught_ARM"]

# Let's check exact bone head->child directions in world space after scale=1.725 and Z+90 rotation
scale_f = 1.725
rot_z90 = mathutils.Matrix.Rotation(math.radians(90), 4, 'Z')
scale_m = mathutils.Matrix.Scale(scale_f, 4)
xf = rot_z90 @ scale_m @ ons_arm.matrix_world

def bpos(name):
    return xf @ ons_arm.data.bones[name].head_local

for pair in [
    ("bip_collar_L", "bip_upperArm_L"),
    ("bip_upperArm_L", "bip_lowerArm_L"),
    ("bip_lowerArm_L", "bip_hand_L"),
    ("bip_hip_L", "bip_knee_L"),
    ("bip_knee_L", "bip_foot_L"),
    ("bip_foot_L", "bip_toe_L"),
]:
    p0 = bpos(pair[0])
    p1 = bpos(pair[1])
    dv = p1 - p0
    print(f"{pair[0]:16s} -> {pair[1]:16s}: d=({dv.x:6.3f}, {dv.y:6.3f}, {dv.z:6.3f}) len={dv.length:.3f}")

# Check chest badge 4 polygons vs chest surface
chest = bpy.data.objects["RB_Onslaught_CHARSKEL_Chest.mo.dmx"]
for poly in chest.data.polygons:
    if poly.material_index == 1:
        verts = [xf @ chest.data.vertices[vi].co for vi in poly.vertices]
        cx = sum(v.x for v in verts)/len(verts)
        cy = sum(v.y for v in verts)/len(verts)
        cz = sum(v.z for v in verts)/len(verts)
        print(f"Chest Logo poly {poly.index}: center=({cx:.3f}, {cy:.3f}, {cz:.3f}) normal={poly.normal}")

# Check HeavyMG slot[0] bounding box in world space (after scale + Z90)
hmg_l = bpy.data.objects["RB_HeavyMGL_SKEL.mo.dmx"]
slot0_verts = set()
for poly in hmg_l.data.polygons:
    if poly.material_index == 0:
        for vi in poly.vertices:
            slot0_verts.add(vi)
pts = [xf @ hmg_l.data.vertices[vi].co for vi in slot0_verts]
xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
print(f"HeavyMGL slot[0] ({len(pts)} verts): X[{min(xs):.3f}, {max(xs):.3f}] Y[{min(ys):.3f}, {max(ys):.3f}] Z[{min(zs):.3f}, {max(zs):.3f}]")
