import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\megatron_tank_21_authoritative_bindposes.json")
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

print("Megatron Tank Bones:")
for bname, b in d["bones"].items():
    pos = b["unity_world_pos"]
    print(f"  {bname:35s} pos: {pos}")
