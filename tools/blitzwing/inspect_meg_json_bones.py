import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

print("Megatron bone positions in JSON:")
for bname in ['Head', 'Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand']:
    info = meg_data["bones"].get(bname)
    if info:
        print(f"  {bname:14s}: parent={info.get('parent')} | pos={info.get('unity_world_pos')}")
    else:
        print(f"  {bname:14s}: NOT IN JSON!")
