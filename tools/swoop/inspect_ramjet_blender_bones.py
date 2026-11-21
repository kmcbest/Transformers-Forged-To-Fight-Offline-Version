import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

BP_PATH = Path(r"e:\Agent\TFTF-blender\tools\swoop\ramjet_78_authoritative_bindposes.json")
with open(BP_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total bones: {data['bone_count']}")
for name, b in data["bones"].items():
    ux, uy, uz = b["unity_world_pos"]
    # Blender: bx = -ux, by = -uz, bz = uy
    bx, by, bz = -ux, -uz, uy
    print(f"  {name:20s} parent={b['parent']:18s} Blender=({bx:+7.3f}, {by:+7.3f}, {bz:+7.3f})")
