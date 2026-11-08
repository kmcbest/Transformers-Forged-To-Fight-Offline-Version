import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

print(f"=== Objects in {blend_path.name} ===")
for obj in bpy.data.objects:
    print(f"[{obj.type}] {obj.name} (parent: {obj.parent.name if obj.parent else None})")
    if obj.type == 'MESH':
        mats = [s.material.name if s.material else "None" for s in obj.material_slots]
        vgs = [vg.name for vg in obj.vertex_groups]
        print(f"   Mesh: verts={len(obj.data.vertices)}, polys={len(obj.data.polygons)}, mats={mats}")
        print(f"   VGs ({len(vgs)}): {vgs[:8]}...")
    elif obj.type == 'ARMATURE':
        print(f"   Bones ({len(obj.data.bones)}): {[b.name for b in obj.data.bones[:10]]}...")
