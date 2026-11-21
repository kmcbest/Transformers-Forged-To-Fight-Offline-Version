import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_p))

for o in bpy.data.objects:
    if o.type == "MESH":
        print(f"Object: {o.name}")
        print(f"  Material slots ({len(o.material_slots)}): {[s.name for s in o.material_slots]}")
        mat_counts = {}
        for p in o.data.polygons:
            mat_counts[p.material_index] = mat_counts.get(p.material_index, 0) + 1
        print(f"  Polygon material distribution: {mat_counts}")
