import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_src = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_src))

swoop_mesh = bpy.data.objects.get("Swoop.001")
for vg in swoop_mesh.vertex_groups:
    if "Clavicle" in vg.name or "UpperArm" in vg.name:
        verts = [v for v in swoop_mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.3]
        if verts:
            xs = [v.co.x for v in verts]
            ys = [v.co.y for v in verts]
            zs = [v.co.z for v in verts]
            print(f"{vg.name}: {len(verts)} verts, X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
