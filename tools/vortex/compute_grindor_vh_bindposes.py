import json
import sys
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_01_bindposes.json", "r", encoding="utf-8") as f:
    bp_data = json.load(f)

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_bones.json", "r", encoding="utf-8") as f:
    bone_names = json.load(f)

bindposes = bp_data["m_BindPose"]
hashes = bp_data["m_BoneNameHashes"]

print(f"Total vehicle bindposes: {len(bindposes)}, bone names: {len(bone_names)}")

authoritative_data = {}
for i, name in enumerate(bone_names):
    bp_dict = bindposes[i]
    mat = np.zeros((4, 4), dtype=np.float64)
    for r in range(4):
        for c in range(4):
            mat[r, c] = bp_dict[f"e{r}{c}"]
    
    world_mat = np.linalg.inv(mat)
    pos = world_mat[:3, 3]
    authoritative_data[name] = {
        "index": i,
        "hash": hashes[i],
        "bindpose": bp_dict,
        "world_pos": {
            "x": float(pos[0]),
            "y": float(pos[1]),
            "z": float(pos[2])
        }
    }
    if any(k in name.lower() for k in ["rotor", "tail", "body", "wing", "gun", "missile"]):
        print(f"  [{i:2d}] {name:25s}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_authoritative_bindposes.json", "w", encoding="utf-8") as f:
    json.dump(authoritative_data, f, indent=2)

print("Saved grindor_45_vh_authoritative_bindposes.json successfully!")
