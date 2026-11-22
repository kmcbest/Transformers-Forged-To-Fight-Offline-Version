import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np
from mathutils import Vector

DONOR_JSON = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")

def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))

donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
mesh_00 = donor["meshes"]["cha_megatronus_gs_kabam_00"]
avatar_tos = donor["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]

pos_b = {}
for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ])
    inv_mat = np.linalg.inv(mat)
    upos = inv_mat[:3, 3]
    bname = avatar_tos.get(str(h), f"bone_{idx}").split("/")[-1]
    pos_b[bname] = (upos, unity_to_blender(upos))

print("=== Bone Positions for Left/Right Limbs ===")
for bname in ["LeftArm", "RightArm", "LeftHand", "RightHand", "LeftUpLeg", "RightUpLeg"]:
    upos, bpos = pos_b[bname]
    print(f"{bname:15s} | Unity: [{upos[0]:7.3f}, {upos[1]:7.3f}, {upos[2]:7.3f}] | Blender: [{bpos.x:7.3f}, {bpos.y:7.3f}, {bpos.z:7.3f}]")
