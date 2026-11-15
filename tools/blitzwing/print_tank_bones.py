import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"E:\Agent\TFTF-blender\tools\blitzwing\megatron_tank_21_authoritative_bindposes.json", "r") as f:
    d = json.load(f)

for b in d.get("bones", []):
    print(b.get("name"), b.get("matrix"))
