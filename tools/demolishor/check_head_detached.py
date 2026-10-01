# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

head_verts = [v for v in mesh.data.vertices if any("Head" in mesh.vertex_groups[g.group].name or "Face" in mesh.vertex_groups[g.group].name for g in v.groups)]
print(f"Total head/face vertices: {len(head_verts)}")

# Check connected polygons
mesh.data.update()
head_vert_indices = set(v.index for v in head_verts)
connected_to_body = 0
for poly in mesh.data.polygons:
    in_head = sum(1 for vi in poly.vertices if vi in head_vert_indices)
    if 0 < in_head < len(poly.vertices):
        connected_to_body += 1

print(f"Polygons connecting head to body: {connected_to_body}")
if connected_to_body == 0:
    print("[*] The head is a 100% COMPLETELY DETACHED loose part!")
else:
    print(f"[*] The head shares {connected_to_body} polygons with the neck/body.")
