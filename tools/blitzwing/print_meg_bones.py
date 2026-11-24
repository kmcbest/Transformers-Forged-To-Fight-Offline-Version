import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

p = Path(r"e:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json")
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

bones = data.get("bone_names", [])
print(f"Total bones: {len(bones)}")
print("Bones:")
for b in bones:
    print(f"  {b}")
