import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open("tools/swoop/ramjet_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    donor = json.load(f)

for bname in ["Head", "Hips", "LeftHand", "RightHand", "LeftFoot", "RightFoot"]:
    u_pos = donor["bones"][bname]["unity_world_pos"]
    print(f"Donor {bname:10s} Unity: X={u_pos[0]:+.3f}, Y={u_pos[1]:+.3f}, Z={u_pos[2]:+.3f}")
