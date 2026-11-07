import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

master_blend = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))

all_vgs = {}
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        vgs = [vg.name for vg in obj.vertex_groups]
        all_vgs[obj.name] = vgs

print(f"=== ALL MESH OBJECTS AND VERTEX GROUPS ===")
unique_vg_names = set()
for obj_name, vgs in all_vgs.items():
    print(f"\nObject: {obj_name} ({len(vgs)} VGs)")
    print(f"  {vgs}")
    unique_vg_names.update(vgs)

print(f"\nTotal unique vertex group names across all parts: {len(unique_vg_names)}")
for vg in sorted(unique_vg_names):
    print(f"  - {vg}")
