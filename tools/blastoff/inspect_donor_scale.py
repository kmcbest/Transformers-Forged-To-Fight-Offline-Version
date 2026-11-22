import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import numpy as np
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")
data = json.loads(p.read_text(encoding="utf-8"))
mesh_00 = data["meshes"]["cha_megatronus_gs_kabam_00"]
avatar_tos = data["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]

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
    # Blender (-ux, -uz, uy)
    pos_b[bname] = (-float(upos[0]), -float(upos[2]), float(upos[1]))

print("Megatronus Donor Bone Positions (Blender space: +X=Left, -Y=Fwd, +Z=Up):")
for k in ["Hips", "Spine", "Spine1", "Neck", "Head", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandIndex1", "LeftHandThumb1", "LeftLeg", "LeftFoot"]:
    p = pos_b.get(k)
    if p:
        print(f"  {k:15s}: ({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})")
