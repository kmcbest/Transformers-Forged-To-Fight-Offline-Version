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
mesh = car.data

# Find wheels by geometry or loose islands
# Let's separate loose parts to see if wheels are separate mesh islands
bpy.context.view_layer.objects.active = car
bpy.ops.object.select_all(action='DESELECT')
car.select_set(True)
bpy.ops.mesh.separate(type='LOOSE')

parts = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Total separate loose parts: {len(parts)}")
for p in sorted(parts, key=lambda o: len(o.data.vertices), reverse=True):
    bb = p.dimensions
    print(f"  Part '{p.name}': {len(p.data.vertices)} verts, {len(p.data.polygons)} polys, dims={bb}, loc={p.location}")
