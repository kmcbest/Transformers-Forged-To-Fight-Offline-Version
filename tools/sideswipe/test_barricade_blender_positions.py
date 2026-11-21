import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import numpy as np

SUMMARY_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\donor_summary.json"

with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
    donor = json.load(f)

mesh_00 = donor["meshes"]["cha_barricade_cin_dotm_00"]
av_00 = donor["avatars"]["cha_barricade_cin_dotm_00Avatar"]
tos_00 = av_00["tos"]

def unity_to_blender(upos):
    return np.array([-float(upos[0]), -float(upos[2]), float(upos[1])])

print("Barricade 77 Bones in Blender Space (Left=+X, Right=-X, Fwd=-Y, Up=+Z):")
key_bones = ["Hips", "Spine", "Spine1", "Neck", "Head", 
             "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
             "LeftHandThumb1", "LeftHandIndex1", "LeftHandMiddle1",
             "RightShoulder", "RightArm", "RightForeArm", "RightHand",
             "RightHandThumb1", "RightHandIndex1", "RightHandMiddle1",
             "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
             "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"]

for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
    ])
    inv_mat = np.linalg.inv(mat)
    upos = inv_mat[:3, 3]
    h_str = str(h)
    bpath = tos_00.get(h_str, "")
    bname = bpath.split("/")[-1] if bpath else f"bone_{idx}"
    bpos = unity_to_blender(upos)
    if bname in key_bones or "Thumb" in bname or "Index" in bname:
        print(f"  {bname:20s}: Blender pos = ({bpos[0]:6.3f}, {bpos[1]:6.3f}, {bpos[2]:6.3f})")
