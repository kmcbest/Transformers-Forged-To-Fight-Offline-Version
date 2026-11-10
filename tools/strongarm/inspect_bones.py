import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r'E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json', 'r', encoding='utf-8') as f:
    rig = json.load(f)

print(f"Prowl rig bone count: {len(rig)}")
for i, b in enumerate(rig):
    print(f"{i:2d}: {b['name']}")
