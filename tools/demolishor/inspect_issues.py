# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
mesh = bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

print("=== Head / Neck Bones in Armature ===")
for b in arm.pose.bones:
    if any(k in b.name.lower() for k in ["head", "neck", "jaw", "eye", "ear"]):
        h = arm.matrix_world @ b.head
        t = arm.matrix_world @ b.tail
        print(f"  {b.name:20s}: head=(X={h.x:6.2f}, Y={h.y:6.2f}, Z={h.z:6.2f}) tail=(X={t.x:6.2f}, Y={t.y:6.2f}, Z={t.z:6.2f})")

print("\n=== Demolishor Head Mesh Vertices ===")
# Check head vertex groups
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "neck"])]
head_pts = [v.co for v in mesh.data.vertices if any(g.group in head_vgs and g.weight > 0.4 for g in v.groups)]
if head_pts:
    ch = sum(head_pts, mathutils.Vector()) / len(head_pts)
    min_z = min(p.z for p in head_pts)
    max_z = max(p.z for p in head_pts)
    min_y = min(p.y for p in head_pts)
    max_y = max(p.y for p in head_pts)
    print(f"  Demolishor Head center: (X={ch.x:.2f}, Y={ch.y:.2f}, Z={ch.z:.2f})")
    print(f"  Demolishor Head span Z: [{min_z:.2f}, {max_z:.2f}], span Y: [{min_y:.2f}, {max_y:.2f}]")

# Check all parts bound to LeftUpLeg or RightUpLeg that have Z > 5.0 (waist area!)
print("\n=== Parts bound to UpLeg that are high up (Z > 5.0) ===")
# We can find vertices with group RightUpLeg or LeftUpLeg at Z > 5.0
r_upleg_idx = mesh.vertex_groups.get("RightUpLeg")
l_upleg_idx = mesh.vertex_groups.get("LeftUpLeg")

if r_upleg_idx:
    high_r = [v for v in mesh.data.vertices if v.co.z > 5.0 and any(g.group == r_upleg_idx.index and g.weight > 0.5 for g in v.groups)]
    print(f"  RightUpLeg verts with Z > 5.0: {len(high_r)}")
    if high_r:
        cz = sum(v.co.z for v in high_r)/len(high_r)
        cy = sum(v.co.y for v in high_r)/len(high_r)
        cx = sum(v.co.x for v in high_r)/len(high_r)
        print(f"    Center: (X={cx:.2f}, Y={cy:.2f}, Z={cz:.2f})")

if l_upleg_idx:
    high_l = [v for v in mesh.data.vertices if v.co.z > 5.0 and any(g.group == l_upleg_idx.index and g.weight > 0.5 for g in v.groups)]
    print(f"  LeftUpLeg verts with Z > 5.0: {len(high_l)}")
    if high_l:
        cz = sum(v.co.z for v in high_l)/len(high_l)
        cy = sum(v.co.y for v in high_l)/len(high_l)
        cx = sum(v.co.x for v in high_l)/len(high_l)
        print(f"    Center: (X={cx:.2f}, Y={cy:.2f}, Z={cz:.2f})")
