import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np

DONOR_JSON = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")
donor = json.loads(DONOR_JSON.read_text(encoding='utf-8'))
mesh_01 = donor['meshes']['cha_megatronus_gs_kabam_01']
hashes = mesh_01['boneHashes']
idx = hashes.index(2689225236)
bp = mesh_01['bindposes'][idx]

mat = np.array([
    [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
    [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
    [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
    [bp['e30'], bp['e31'], bp['e32'], bp['e33']],
])

inv_mat = np.linalg.inv(mat)
upos = inv_mat[:3, 3]

print(f"chop1_torso_center Unity pos: {upos}")
# Convert to Blender right-handed (-ux, -uz, uy)
b_pos = (-upos[0], -upos[2], upos[1])
print(f"chop1_torso_center Blender pos: {b_pos}")
