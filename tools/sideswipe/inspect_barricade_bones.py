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

print(f"=== Barricade 00 Robot Mesh ({len(mesh_00['bindposes'])} bones) ===")
bone_list = []
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
    bpath = tos_00.get(h_str, "UNKNOWN")
    bname = bpath.split("/")[-1] if bpath else f"bone_{idx}"
    bone_list.append((idx, bname, bpath, pos, inv_mat))
    print(f"[{idx:2d}] {bname:25s}: pos=({pos[0]:7.3f}, {pos[1]:7.3f}, {pos[2]:7.3f}) path={bpath}")

print("\n=== Barricade 01 Car Mesh ===")
mesh_01 = donor["meshes"]["cha_barricade_cin_dotm_01"]
av_01 = donor["avatars"]["cha_barricade_cin_dotm_01Avatar"]
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
    print(f"[{idx:2d}] {bname:25s}: pos=({pos[0]:7.3f}, {pos[1]:7.3f}, {pos[2]:7.3f})")
