import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

for obj in bpy.data.objects:
    if obj.type == "MESH":
        print(f"\nMesh Object: {obj.name}, verts: {len(obj.data.vertices)}")
        for vg in obj.vertex_groups:
            v_count = 0
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.01:
                        v_count += 1
                        break
            print(f"  VG [{vg.index:2d}] '{vg.name}': {v_count} verts")
