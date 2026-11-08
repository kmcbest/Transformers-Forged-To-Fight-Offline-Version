import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

bp_data = json.loads(Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json").read_text(encoding="utf-8"))

for bname in ["Hips", "Head", "LeftHand", "RightHand", "LeftFoot", "RightFoot"]:
    pos = bp_data[bname]["world_pos"]
    print(f"Grindor {bname:12s}: Unity (x={pos['x']:6.3f}, y={pos['y']:6.3f}, z={pos['z']:6.3f})")
    # If Blender (ux, uz, uy):
    print(f"         Blender (x={pos['x']:6.3f}, y={pos['z']:6.3f}, z={pos['y']:6.3f})")
