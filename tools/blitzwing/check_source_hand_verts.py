import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC))

mesh = None
for o in bpy.data.objects:
    if o.type == 'MESH':
        mesh = o
        break

print(f"Mesh: {mesh.name if mesh else None}")
if mesh:
    vgs = {vg.index: vg.name for vg in mesh.vertex_groups}
    finger_vgs = [name for name in vgs.values() if "finger" in name.lower() or "hand" in name.lower()]
    print(f"Finger/Hand VGs ({len(finger_vgs)}):")
    for name in sorted(finger_vgs):
        vg = mesh.vertex_groups[name]
        # count vertices with weight > 0
        cnt = sum(1 for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01)
        print(f"  {name}: {cnt} verts")
