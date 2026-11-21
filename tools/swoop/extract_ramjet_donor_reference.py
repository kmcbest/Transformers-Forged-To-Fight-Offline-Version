import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\tools\swoop")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== Extracting Ramjet Donor Ground Truth from {DONOR_BUNDLE} ===")
env = UnityPy.load(str(DONOR_BUNDLE))

go_names = {}
transforms = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        d = obj.read()
        go_names[obj.path_id] = d.m_Name
    elif obj.type.name == "Transform":
        t = obj.read_typetree()
        transforms[obj.path_id] = t

tr_to_name = {}
for tr_id, tr in transforms.items():
    go_id = tr.get("m_GameObject", {}).get("m_PathID")
    tr_to_name[tr_id] = go_names.get(go_id, f"Unknown_{go_id}")

# 1. Robot SMR (78 bones)
robot_smr = None
jet_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        n_bones = len(tree.get("m_Bones", []))
        if n_bones == 78 and not robot_smr:
            robot_smr = tree
        elif n_bones == 29 and not jet_smr:
            jet_smr = tree

def extract_smr_data(smr_tree, out_name):
    bone_pids = [b["m_PathID"] for b in smr_tree["m_Bones"]]
    bone_names = [tr_to_name.get(pid, f"Bone_{idx}") for idx, pid in enumerate(bone_pids)]
    mesh_pid = smr_tree["m_Mesh"]["m_PathID"]
    mesh_obj = [o for o in env.objects if o.path_id == mesh_pid][0]
    mesh_tree = mesh_obj.read_typetree()
    bp_list = mesh_tree.get("m_BindPose", [])
    
    bones_info = {}
    for idx, (bname, pid) in enumerate(zip(bone_names, bone_pids)):
        bp = bp_list[idx]
        mat = np.array([
            [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
            [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
            [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
            [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
        ])
        inv_mat = np.linalg.inv(mat)
        pos = inv_mat[:3, 3].tolist()
        tr = transforms.get(pid, {})
        parent_tr_id = tr.get("m_Father", {}).get("m_PathID", 0)
        parent_name = tr_to_name.get(parent_tr_id, "None")
        bones_info[bname] = {
            "index": idx,
            "path_id": pid,
            "parent": parent_name,
            "unity_world_pos": pos,
            "bind_pose_matrix": {f"e{r}{c}": float(bp[f"e{r}{c}"]) for r in range(4) for c in range(4)}
        }
    
    out_dict = {
        "bone_count": len(bone_names),
        "bone_names": bone_names,
        "bones": bones_info,
        "local_aabb": mesh_tree.get("m_LocalAABB", {}),
        "mesh_name": mesh_tree.get("m_Name", ""),
        "bone_name_hashes": mesh_tree.get("m_BoneNameHashes", [])
    }
    out_file = OUT_DIR / out_name
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)
    print(f"[✓] Saved {out_file} ({len(bone_names)} bones)")
    return mesh_tree

if robot_smr:
    robot_mesh = extract_smr_data(robot_smr, "ramjet_78_authoritative_bindposes.json")
if jet_smr:
    jet_mesh = extract_smr_data(jet_smr, "ramjet_jet_29_authoritative_bindposes.json")

print("[✓] Ramjet donor ground truth extracted successfully.")
