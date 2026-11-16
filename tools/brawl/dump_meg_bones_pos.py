import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from pathlib import Path

with open(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\donor_summary.json", "r", encoding="utf-8") as f:
    donor = json.load(f)

mesh_00 = donor["meshes"]["cha_megatron_cin_rotf_00"]
av = donor["avatars"]["cha_megatron_cin_rotf_00Avatar"]
tos = av["tos"]

print("Megatron 00 Bones:")
for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
    ])
    inv_mat = np.linalg.inv(mat)
    pos = inv_mat[:3, 3]
    h_str = str(h)
    bpath = tos.get(h_str, "UNKNOWN")
    bname = bpath.split("/")[-1] if bpath else f"bone_{idx}"
    print(f"[{idx:2d}] {bname:20s}: pos=({pos[0]:6.3f}, {pos[1]:6.3f}, {pos[2]:6.3f})")

print("\nMegatron 01 Tank Bounds & Bones:")
mesh_01 = donor["meshes"]["cha_megatron_cin_rotf_01"]
av_01 = donor["avatars"]["cha_megatron_cin_rotf_01Avatar"]
tos_01 = av_01["tos"]
for idx, (h, bp) in enumerate(zip(mesh_01["boneHashes"], mesh_01["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
    ])
    inv_mat = np.linalg.inv(mat)
    pos = inv_mat[:3, 3]
    h_str = str(h)
    bpath = tos_01.get(h_str, "UNKNOWN")
    bname = bpath.split("/")[-1] if bpath else f"bone_{idx}"
    if "cog" in bname.lower() or idx in [0, 21]:
        print(f"[{idx:2d}] {bname:20s}: pos=({pos[0]:6.3f}, {pos[1]:6.3f}, {pos[2]:6.3f})")
