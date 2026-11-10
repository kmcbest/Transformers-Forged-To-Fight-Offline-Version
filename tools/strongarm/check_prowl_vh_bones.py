import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np

with open(r'E:\Agent\TFTF-blender\tools\strongarm\prowl_vehicle_rig.json', 'r', encoding='utf-8') as f:
    vh_bones = json.load(f)

for b in vh_bones:
    bp = b["bindpose"]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    pos = inv[:3, 3]
    print(f"Vehicle bone {b['name']:25s}: Unity pos = (X={pos[0]:6.3f}, Y={pos[1]:6.3f}, Z={pos[2]:6.3f})")
