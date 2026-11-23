import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from mathutils import Vector

def u_to_b(pos):
    return Vector((pos[0], -pos[2], pos[1]))

p = Path(r"e:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json")
with open(p, "r", encoding="utf-8") as f:
    meg_51_data = json.load(f)

for side, pfx in [("L", "Left"), ("R", "Right")]:
    for fname in ["Index1", "Index2", "Index3", "Thumb1", "Thumb2", "Thumb3"]:
        bname = f"{pfx}Hand{fname}"
        b_info = meg_51_data["bones"][bname]
        head = u_to_b(b_info["unity_world_pos"])
        parent = b_info.get("parent")
        print(f"{bname}: head={head}, parent={parent}")
