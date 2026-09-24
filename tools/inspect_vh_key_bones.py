# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("tools/demolishor/ironhide_47_vh_bones.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for b in ["BodyBase", "chop1_hip", "chop2_torso_main", "chop1_torso_back_main"]:
    if b in d["bones"]:
        m = d["bones"][b]["matrix"]
        print(f"{b:25s}: pos=({m[0][3]:7.2f}, {m[1][3]:7.2f}, {m[2][3]:7.2f})")
