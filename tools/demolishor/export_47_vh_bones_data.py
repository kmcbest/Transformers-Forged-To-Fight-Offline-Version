# -*- coding: utf-8 -*-
import json
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# 1. Get the 47 bindposes of cha_ironhide_cin_rotf_01
bindposes_data = []
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_01':
            bindposes_data = tree.get('m_BindPose', [])
            break

# 2. Get the 47 bone names in SMR order
go_names = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')

path_to_name = {}
for obj in env.objects:
    if obj.type.name == 'Transform':
        t = obj.read_typetree()
        go_pid = t.get('m_GameObject', {}).get('m_PathID')
        path_to_name[obj.path_id] = go_names.get(go_pid, f"Unknown_{go_pid}")

target_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_ptr = tree.get("m_Mesh", {})
        for m_obj in env.objects:
            if m_obj.path_id == mesh_ptr.get("m_PathID") and m_obj.type.name == "Mesh":
                if m_obj.read_typetree().get("m_Name") == "cha_ironhide_cin_rotf_01":
                    target_smr = tree
                    break
        if target_smr:
            break

bones_ptrs = target_smr.get("m_Bones", [])
bone_order = [path_to_name.get(b.get("m_PathID")) for b in bones_ptrs]

print(f"Total vehicle bones: {len(bone_order)}, bindposes: {len(bindposes_data)}")

# 3. Compute world matrix for each of the 47 bones
bones_dict = {}
for idx, name in enumerate(bone_order):
    bp = bindposes_data[idx]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv_mat = np.linalg.inv(mat)
    bones_dict[name] = {
        "index": idx,
        "name": name,
        "matrix": inv_mat.tolist()
    }

out_path = "tools/demolishor/ironhide_47_vh_bones.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "bone_order": bone_order,
        "bones": bones_dict
    }, f, indent=2)

print(f"[✓] Saved {len(bones_dict)} vehicle bones to {out_path}")
