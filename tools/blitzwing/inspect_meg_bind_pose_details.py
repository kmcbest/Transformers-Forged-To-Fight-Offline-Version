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

for bname in ["LeftHand", "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3"]:
    info = data["bones"].get(bname, {})
    print(f"Bone '{bname}':")
    print(f"  parent: {info.get('parent')}")
    print(f"  unity_world_pos: {info.get('unity_world_pos')}")
    print(f"  bind_pose_matrix: {info.get('bind_pose_matrix')}")
