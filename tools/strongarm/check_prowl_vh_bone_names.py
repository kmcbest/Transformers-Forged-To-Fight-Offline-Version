import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r'E:\Agent\TFTF-blender\tools\strongarm\prowl_vehicle_rig.json', 'r', encoding='utf-8') as f:
    bones = json.load(f)

print(f"Vehicle bones ({len(bones)}):")
for b in bones:
    print(f"  {b['name']}")
