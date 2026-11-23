import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json")
data = json.loads(p.read_text(encoding="utf-8"))
print("Bones in megatron_51:")
for b in data["bone_names"]:
    if any(k in b for k in ["Hand", "Thumb", "Index", "Middle", "Ring", "Pinky"]):
        pos = data["bones"][b]["unity_world_pos"]
        print(f"  {b}: {pos}")
