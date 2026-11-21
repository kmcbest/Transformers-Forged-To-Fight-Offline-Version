import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

BP_JSON = Path("e:/Agent/TFTF-blender/tools/swoop/ramjet_78_authoritative_bindposes.json")
with open(BP_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

for b in ["LeftShoulder", "LeftShoulderPad", "LeftArm", "LeftForeArm", "RightShoulder", "RightShoulderPad", "RightArm"]:
    if b in data["bones"]:
        info = data["bones"][b]
        print(f"{b}: parent={info['parent']}, pos={info['unity_world_pos']}")
