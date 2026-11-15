import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"E:\Agent\TFTF-blender\tools\blitzwing\megatron_tank_21_authoritative_bindposes.json", "r") as f:
    d = json.load(f)

print("bone_names:", d.get("bone_names"))
print("bones type:", type(d.get("bones")))
if isinstance(d.get("bones"), dict):
    for k, v in d["bones"].items():
        print(f" {k}: {v}")
elif isinstance(d.get("bones"), list):
    print("first 3 bones:", d["bones"][:3])
