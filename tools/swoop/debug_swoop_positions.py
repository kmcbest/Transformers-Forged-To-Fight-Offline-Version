import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

for obj in bpy.context.scene.objects:
    print(f"Obj: {obj.name}, type: {obj.type}, parent: {obj.parent.name if obj.parent else None}")
    print(f"  matrix_world loc: {obj.matrix_world.to_translation()}, scale: {obj.matrix_world.to_scale()}")
    if obj.type == 'MESH':
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        print(f"  bounds X: [{min(xs):.3f}, {max(xs):.3f}], Y: [{min(ys):.3f}, {max(ys):.3f}], Z: [{min(zs):.3f}, {max(zs):.3f}]")
        
        # Check vertex groups related to Hand
        for vg in obj.vertex_groups:
            if "Hand" in vg.name or "hand" in vg.name:
                v_in_g = [pts[v.index] for v in obj.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
                if v_in_g:
                    mean_p = sum(v_in_g, Vector((0,0,0))) / len(v_in_g)
                    print(f"    VG {vg.name} ({len(v_in_g)} verts) world mean: {mean_p}")
