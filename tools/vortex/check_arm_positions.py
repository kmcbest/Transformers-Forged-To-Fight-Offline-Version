import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

bp_data = json.loads(Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json").read_text(encoding="utf-8"))
g_b_pos = {}
for bname, info in bp_data.items():
    p = info["world_pos"]
    g_b_pos[bname] = (p["x"], p["z"], p["y"])

print("=== Grindor Arm & Hand Positions (Blender) ===")
for b in ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
          "LeftHandIndex1", "LeftHandMiddle1", "LeftHandRing1", "LeftHandPinky1", "LeftHandThumb1"]:
    p = g_b_pos[b]
    print(f"  {b:18s}: ({p[0]:6.3f}, {p[1]:6.3f}, {p[2]:6.3f})")
