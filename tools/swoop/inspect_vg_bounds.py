import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

swoop = bpy.data.objects.get("Swoop.001")
mw = swoop.matrix_world
pts = [mw @ v.co for v in swoop.data.vertices]

print(f"Total verts: {len(pts)}")
for vg in swoop.vertex_groups:
    v_in_g = [pts[v.index] for v in swoop.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if v_in_g:
        xs = [p.x for p in v_in_g]
        ys = [p.y for p in v_in_g]
        zs = [p.z for p in v_in_g]
        print(f"VG {vg.name:25s} ({len(v_in_g):4d} verts): X=[{min(xs):.3f},{max(xs):.3f}], Y=[{min(ys):.3f},{max(ys):.3f}], Z=[{min(zs):.3f},{max(zs):.3f}]")
