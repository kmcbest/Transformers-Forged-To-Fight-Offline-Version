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
print("Hand vertex groups in Swoop.001:")
for vg in swoop_mesh.vertex_groups:
    if "Hand" in vg.name or "Finger" in vg.name:
        verts = [v for v in swoop_mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01]
        print(f"  {vg.name}: {len(verts)} vertices")
