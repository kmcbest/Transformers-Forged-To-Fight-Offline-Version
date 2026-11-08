import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    bps = json.load(f)

for name in ["Hips", "Head", "LeftHand", "RightHand", "LeftFoot", "RightFoot", "RightForeArm", "LeftForeArm"]:
    if name in bps:
        wp = bps[name]['world_pos']
        print(f"{name:15}: x={wp['x']:8.3f}, y={wp['y']:8.3f}, z={wp['z']:8.3f}")
