# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
mesh = bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

print("=== Ironhide Head & Facial Bones in World Space ===")
for b in arm.pose.bones:
    if any(k in b.name.lower() for k in ["head", "eye", "lid", "jaw", "neck"]):
        h = arm.matrix_world @ b.head
        t = arm.matrix_world @ b.tail
        print(f"  {b.name:18s}: head=(Y={h.y:6.2f}, Z={h.z:6.2f}) tail=(Y={t.y:6.2f}, Z={t.z:6.2f})")

print("\n=== Demolishor Face / Head Mesh Vertices ===")
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "neck", "jaw"])]
head_pts = [v.co for v in mesh.data.vertices if any(g.group in head_vgs for g in v.groups)]

# Also find the front-most vertices of the face/visor/chin
min_y = min(p.y for p in head_pts)
max_y = max(p.y for p in head_pts)
print(f"Demolishor Head Span Y: [{min_y:.2f}, {max_y:.2f}]")

# Check which direction is the front of the character (e.g. where the toes point or chest faces)
toes = [b for b in arm.pose.bones if "toe" in b.name.lower()]
for b in toes:
    h = arm.matrix_world @ b.head
    t = arm.matrix_world @ b.tail
    print(f"  Toe {b.name}: head Y={h.y:.2f} -> tail Y={t.y:.2f} (Forward direction is along {'+Y' if t.y > h.y else '-Y'})")
