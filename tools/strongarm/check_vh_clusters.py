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
car.rotation_euler = (0, 0, 3.1415926)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
car.scale = (1.0, 1.45168, 1.073)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.type == 'MESH']

# Find parts that have circular shapes or wheels
for p in parts:
    verts = p.data.vertices
    if len(verts) > 10:
        cx = sum(v.co.x for v in verts) / len(verts)
        cy = sum(v.co.y for v in verts) / len(verts)
        cz = sum(v.co.z for v in verts) / len(verts)
        if cz < 0.8: # low to ground
            if abs(cx) > 0.8: # on left or right side
                print(f"Low outer part {p.name:20s}: C=({cx:6.3f}, {cy:6.3f}, {cz:6.3f}), verts={len(verts)}")
