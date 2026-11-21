import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json

SUMMARY_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\donor_summary.json"

with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
    donor = json.load(f)

mesh_00 = donor["meshes"]["cha_barricade_cin_dotm_00"]
av_00 = donor["avatars"]["cha_barricade_cin_dotm_00Avatar"]
tos_00 = av_00["tos"]

bones_77 = []
parent_map = {}

for idx, h in enumerate(mesh_00["boneHashes"]):
    h_str = str(h)
    bpath = tos_00.get(h_str, "")
    bname = bpath.split("/")[-1] if bpath else f"bone_{idx}"
    parent_name = bpath.split("/")[-2] if "/" in bpath and len(bpath.split("/")) > 1 else None
    if parent_name == "Reference":
        parent_name = None
    bones_77.append(bname)
    parent_map[bname] = parent_name
    print(f"[{idx:2d}] {bname:25s} -> parent: {str(parent_name):20s} (hash={h})")

out_file = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\barricade_77_bones.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({
        "bone_names": bones_77,
        "parent_map": parent_map,
        "bone_hashes": mesh_00["boneHashes"],
        "bindposes": mesh_00["bindposes"],
        "rootBoneHash": mesh_00["rootBoneHash"]
    }, f, indent=2)

print(f"\nSaved {len(bones_77)} bones to {out_file}")
