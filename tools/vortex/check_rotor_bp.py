import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BP_JSON = ROOT / "tools" / "vortex" / "grindor_45_vh_authoritative_bindposes.json"
bp_data = json.loads(BP_JSON.read_text(encoding="utf-8"))

for bname in ["RotorMain", "RotorMainBlade1", "RotorMainBlade2", "RotorMainBlade3", "RotorMainBlade4", "BodyTopCenterRight"]:
    if bname in bp_data:
        info = bp_data[bname]
        print(f"Bone: {bname:20s} pos={info.get('world_pos')}")

