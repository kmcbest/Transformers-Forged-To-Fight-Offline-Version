import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

for o in bpy.data.objects:
    if o.type == 'MESH':
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        print(f"Mesh '{o.name}': {len(o.data.vertices)} verts, {len(o.data.polygons)} polys")
        print(f"  World bounds: X=[{min(xs):.4f}, {max(xs):.4f}], Y=[{min(ys):.4f}, {max(ys):.4f}], Z=[{min(zs):.4f}, {max(zs):.4f}]")
        print(f"  Local bounds: {o.bound_box[0]} to {o.bound_box[6]}")
