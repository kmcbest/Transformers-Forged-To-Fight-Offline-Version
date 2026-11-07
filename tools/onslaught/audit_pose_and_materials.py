import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
import mathutils

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "demolishor" / "ironhide_80_bones.json"
VH_BONES_JSON = ROOT / "tools" / "demolishor" / "ironhide_47_vh_bones.json"
MASTER_BLEND = ROOT / "3rd-party-models" / "onslaught" / "onslaught_master.blend"
IRONHIDE_OBJ = ROOT / "tools" / "demolishor" / "ironhide_extracted" / "ironhide.obj"

bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))

print("=== 1. ALL OBJECTS & MATERIAL SLOTS IN ONSLAUGHT_MASTER.BLEND ===")
for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    if obj.type == 'MESH':
        mats = [s.material.name if s.material else "None" for s in obj.material_slots]
        poly_counts = {}
        uv_layer = obj.data.uv_layers.active
        uv_ranges = {}
        for poly in obj.data.polygons:
            mi = poly.material_index
            poly_counts[mi] = poly_counts.get(mi, 0) + 1
            if uv_layer:
                for li in poly.loop_indices:
                    u, v = uv_layer.data[li].uv
                    if mi not in uv_ranges:
                        uv_ranges[mi] = [u, u, v, v]
                    else:
                        r = uv_ranges[mi]
                        r[0] = min(r[0], u)
                        r[1] = max(r[1], u)
                        r[2] = min(r[2], v)
                        r[3] = max(r[3], v)
        print(f"Mesh: {obj.name} | verts={len(obj.data.vertices)} | parent={obj.parent.name if obj.parent else None}")
        for idx, mname in enumerate(mats):
            cnt = poly_counts.get(idx, 0)
            uvr = uv_ranges.get(idx, [0,0,0,0])
            print(f"  slot[{idx}] {mname}: {cnt} polys | UV U[{uvr[0]:.2f}, {uvr[1]:.2f}] V[{uvr[2]:.2f}, {uvr[3]:.2f}]")

print("\n=== 2. ONSLAUGHT_ARM KEY BONE POSITIONS (AFTER SCALE=1.725, ROT_Z=+90) ===")
ons_arm = bpy.data.objects.get("Onslaught_ARM")
scale_f = 1.725
rot_z90 = mathutils.Matrix.Rotation(math.radians(90), 4, 'Z')
scale_m = mathutils.Matrix.Scale(scale_f, 4)

# Compute min_z of robot body after transform
robot_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and "VH" not in o.name]
min_z = 999.0
max_z = -999.0
for o in robot_meshes:
    mw = rot_z90 @ scale_m @ o.matrix_world
    for v in o.data.vertices:
        wv = mw @ v.co
        min_z = min(min_z, wv.z)
        max_z = max(max_z, wv.z)
print(f"Scaled Onslaught Robot Z range: [{min_z:.3f}, {max_z:.3f}] -> grounded height = {max_z - min_z:.3f}m")

if ons_arm:
    print(f"Onslaught_ARM total bones: {len(ons_arm.data.bones)}")
    mw_arm = rot_z90 @ scale_m @ ons_arm.matrix_world
    for b in ons_arm.data.bones:
        # Print main limb/torso/weapon bones
        if any(k in b.name for k in ["bip_", "Shoulder", "Clav", "Elbow", "Hand", "Hip", "Thigh", "Knee", "Foot", "Head", "Neck", "Spine", "Pelvis", "Lumbar", "Pad", "Weapon", "Gun", "Rocket", "Launcher", "HeavyMG"]):
            bh = mw_arm @ b.head_local - mathutils.Vector((0, 0, min_z))
            bt = mw_arm @ b.tail_local - mathutils.Vector((0, 0, min_z))
            p_name = b.parent.name if b.parent else "None"
            print(f"  OnsBone {b.name:30s} (parent={p_name:25s}): head=({bh.x:6.3f}, {bh.y:6.3f}, {bh.z:6.3f}) tail=({bt.x:6.3f}, {bt.y:6.3f}, {bt.z:6.3f})")

print("\n=== 3. IRONHIDE OFFICIAL 80 BONES IN BLENDER COORDS (X=Right, Y=Forward, Z=Up) ===")
with open(BONES_JSON, "r", encoding="utf-8") as f:
    ih_data = json.load(f)

for bname in ih_data["bone_order"]:
    binfo = ih_data["bones"][bname]
    mat = binfo["matrix"]
    # Check both row-major translation (mat[0][3]...) and Blender Matrix translation
    m = mathutils.Matrix(mat)
    t = m.to_translation()
    # Unity (X, Y, Z) -> Blender (X, Z, Y)
    bx, by, bz = t.x, t.z, t.y
    print(f"  IHBone  {bname:30s} (parent={str(binfo.get('parent')):20s}): pos=({bx:6.3f}, {by:6.3f}, {bz:6.3f})")

print("\n=== 4. CHECK WEAPON VERTEX GROUPS & BOUNDING BOXES ===")
for wname in ["RB_RocketLauncherL_SKEL.mo.dmx", "RB_RocketLauncherR_SKEL.mo.dmx", "RB_HeavyMGL_SKEL.mo.dmx", "RB_HeavyMGR_SKEL.mo.dmx"]:
    wo = bpy.data.objects.get(wname)
    if wo:
        mw = rot_z90 @ scale_m @ wo.matrix_world
        pts = [mw @ v.co - mathutils.Vector((0, 0, min_z)) for v in wo.data.vertices]
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        print(f"Weapon {wname}: X[{min(xs):.3f}, {max(xs):.3f}] Y[{min(ys):.3f}, {max(ys):.3f}] Z[{min(zs):.3f}, {max(zs):.3f}]")
        # Print active vertex groups with non-zero weights
        vg_counts = {}
        for v in wo.data.vertices:
            for g in v.groups:
                if g.weight > 0.01:
                    vgn = wo.vertex_groups[g.group].name
                    vg_counts[vgn] = vg_counts.get(vgn, 0) + 1
        print(f"  Active VGs: {vg_counts}")
