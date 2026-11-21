import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

swoop_mesh = bpy.data.objects.get("Swoop.001")
print(f"Swoop.001 has {len(swoop_mesh.vertex_groups)} vertex groups:")
for vg in swoop_mesh.vertex_groups:
    # count how many vertices have weight > 0.1
    cnt = sum(1 for v in swoop_mesh.data.vertices if any(g.group == vg.index and g.weight > 0.1 for g in v.groups))
    print(f"  {vg.name:<30} ({cnt} verts)")
