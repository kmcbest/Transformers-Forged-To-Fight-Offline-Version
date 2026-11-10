import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=str(obj_path))

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Vehicle mesh objects: {len(mesh_objs)}")
for m in mesh_objs:
    bb = m.dimensions
    print(f"  Mesh: {m.name}, verts: {len(m.data.vertices)}, polys: {len(m.data.polygons)}, dims: {bb}")

# Check materials and textures
for mat in bpy.data.materials:
    print(f"  Material: {mat.name}")
