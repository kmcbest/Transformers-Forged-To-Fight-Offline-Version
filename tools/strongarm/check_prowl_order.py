import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

with open(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json", "r", encoding="utf-8") as f:
    prowl_bones = json.load(f)

prowl_bone_names = [b["name"] for b in prowl_bones]
print("Prowl SMR Bone Order (50 bones):")
for i, bn in enumerate(prowl_bone_names):
    print(f"  [{i:2d}] {bn}")
