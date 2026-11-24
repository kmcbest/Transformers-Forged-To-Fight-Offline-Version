import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
meg_51 = json.loads((ROOT / "tools/blitzwing/megatron_51_authoritative_bindposes.json").read_text(encoding="utf-8"))
for b in ("LeftForeArm", "LeftHand", "LeftHandMiddle1", "LeftHandThumb1", "RightForeArm", "RightHand", "RightHandMiddle1", "RightHandThumb1"):
    if b in meg_51["bones"]:
        print(f"{b:<16}: pos={meg_51['bones'][b]['unity_world_pos']}")
