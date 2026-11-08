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
    print(f"Object: {obj.name}, type: {obj.type}")
    if obj.type == 'MESH':
        for vg in obj.vertex_groups:
            if any(k in vg.name.lower() for k in ["tail", "prop", "rotor", "blade", "spin"]):
                print(f"  VG: {vg.name}")

