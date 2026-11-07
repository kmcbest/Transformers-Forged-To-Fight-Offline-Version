import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

master_blend = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))

head = bpy.data.objects.get("RB_Onslaught_CHARSKEL_Head.mo.dmx")
chest = bpy.data.objects.get("RB_Onslaught_CHARSKEL_Chest.mo.dmx")

print("Head location:", head.location)
print("Head matrix translation:", head.matrix_world.translation)

# Check face polygons center & normal
face_polys = []
for p in head.data.polygons:
    face_polys.append((p.center, p.normal))

# Average normal
avg_normal = sum((n for c, n in face_polys), bpy.data.objects[0].location * 0) / len(face_polys)
print(f"Head average polygon normal: {avg_normal}")

# Find vertex with highest/lowest X and Y
verts = head.data.vertices
min_x = min(v.co.x for v in verts)
max_x = max(v.co.x for v in verts)
min_y = min(v.co.y for v in verts)
max_y = max(v.co.y for v in verts)
print(f"Head vertex X range (depth): [{min_x:.3f}, {max_x:.3f}]")
print(f"Head vertex Y range (width): [{min_y:.3f}, {max_y:.3f}]")
