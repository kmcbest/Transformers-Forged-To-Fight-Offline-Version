# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
mesh = bpy.data.objects.get("cha_demolishor_gs_01")
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "jaw", "face"])]

head_verts = [v for v in mesh.data.vertices if any(g.group in head_vgs for g in v.groups)]
print(f"Total head verts: {len(head_verts)}")

# Sort by Y descending (most forward vertices, i.e. face/visor/chin)
face_verts = sorted(head_verts, key=lambda v: -v.co.y)[:50]
avg_face_y = sum(v.co.y for v in face_verts) / len(face_verts)
avg_face_z = sum(v.co.z for v in face_verts) / len(face_verts)
print(f"Demolishor front face/visor center: Y = {avg_face_y:.2f}, Z = {avg_face_z:.2f}")

# Target: Ironhide's eyes are at Y = 0.56, Z = 9.44
# Head center is at Y = (0.09 + 0.56) / 2 = 0.33, Z = 9.37
print(f"Target Ironhide Face / Eyes: Y = 0.56, Z = 9.44")
print(f"Target Ironhide Head Center: Y = 0.33, Z = 9.37")
print(f"Current Demolishor Head Center Y: {sum(v.co.y for v in head_verts)/len(head_verts):.2f}")
