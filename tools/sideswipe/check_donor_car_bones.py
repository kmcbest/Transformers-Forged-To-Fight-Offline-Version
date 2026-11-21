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

mesh_01 = donor["meshes"]["cha_barricade_cin_dotm_01"]
av_01 = donor["avatars"]["cha_barricade_cin_dotm_01Avatar"]
tos_01 = av_01["tos"]

print(f"Barricade Car Mesh boneCount={mesh_01['boneCount']}, rootBoneHash={mesh_01['rootBoneHash']}")
root_name = tos_01.get(str(mesh_01['rootBoneHash']), "UNKNOWN")
print(f"Root bone name: {root_name}")

print("\nAll Car bones:")
for idx, h in enumerate(mesh_01["boneHashes"]):
    bpath = tos_01.get(str(h), f"bone_{idx}")
    print(f"[{idx:2d}] {bpath}")
