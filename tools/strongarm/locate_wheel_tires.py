import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(obj_path))

car = bpy.data.objects['strongarm_vehicle']
bpy.context.view_layer.objects.active = car
bpy.ops.mesh.separate(type='LOOSE')

parts = [o for o in bpy.data.objects if o.type == 'MESH']

wheel_tires = [o for o in parts if abs(o.dimensions.y - 1.1621) < 0.01 and abs(o.dimensions.z - 1.1621) < 0.01]
print(f"Found {len(wheel_tires)} wheel tires:")
for wt in wheel_tires:
    verts = wt.data.vertices
    cx = sum(v.co.x for v in verts) / len(verts)
    cy = sum(v.co.y for v in verts) / len(verts)
    cz = sum(v.co.z for v in verts) / len(verts)
    print(f"  Tire '{wt.name}': center=({cx:.3f}, {cy:.3f}, {cz:.3f}), dims={wt.dimensions}")
