import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from pathlib import Path

# Load Prowl authoritative rig data
with open(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json", "r", encoding="utf-8") as f:
    prowl_bones = json.load(f)

prowl_bone_positions = {}
for b in prowl_bones:
    bp = b["bindpose"]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    # Unity: (x, y, z)
    prowl_bone_positions[b["name"]] = np.array([inv[0, 3], inv[1, 3], inv[2, 3]])

print(f"Prowl LeftHand Unity pos:  {prowl_bone_positions['LeftHand']}")
print(f"Prowl RightHand Unity pos: {prowl_bone_positions['RightHand']}")
print(f"Prowl LeftForeArm Unity:   {prowl_bone_positions['LeftForeArm']}")
print(f"Prowl RightForeArm Unity:  {prowl_bone_positions['RightForeArm']}")
print(f"Prowl LeftArm Unity:       {prowl_bone_positions['LeftArm']}")
print(f"Prowl RightArm Unity:      {prowl_bone_positions['RightArm']}")
