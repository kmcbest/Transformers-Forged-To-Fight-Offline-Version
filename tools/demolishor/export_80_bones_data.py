import json
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load Ironhide bundle
env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# 2. Get the 80 bindposes
bindposes_data = []
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            bindposes_data = tree.get('m_BindPose', [])
            break

# 3. Get the 80 bone names in order
target_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_ptr = tree.get("m_Mesh", {})
        for m_obj in env.objects:
            if m_obj.path_id == mesh_ptr.get("m_PathID") and m_obj.type.name == "Mesh":
                if m_obj.read_typetree().get("m_Name") == "cha_ironhide_cin_rotf_00":
                    target_smr = tree
                    break
        if target_smr:
            break

path_to_name = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

bones_ptrs = target_smr.get("m_Bones", [])
bone_order = []
for b_ptr in bones_ptrs:
    pid = b_ptr.get("m_PathID")
    name = path_to_name.get(pid, f"Unknown_{pid}")
    bone_order.append(name)

# 4. Get parent-child hierarchy from transforms
with open("tools/demolishor/ironhide_extracted/ironhide_transforms.json", "r", encoding="utf-8") as f:
    transforms = json.load(f)

name_to_parent = {}
for pid, node in transforms.items():
    name = node["name"]
    for c_pid in node.get("children_pids", []):
        c_node = transforms.get(str(c_pid))
        if c_node:
            name_to_parent[c_node["name"]] = name

# 5. Compute world matrix for each of the 80 bones
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
    parent = name_to_parent.get(name)
    # If parent is not in the 80 bones, trace up to an ancestor that is in 80 bones
    cur_p = parent
    while cur_p and cur_p not in bone_order:
        cur_p = name_to_parent.get(cur_p)
    
    bones_dict[name] = {
        "index": idx,
        "name": name,
        "parent": cur_p,
        "matrix": inv_mat.tolist()
    }

out_path = "tools/demolishor/ironhide_80_bones.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "bone_order": bone_order,
        "bones": bones_dict
    }, f, indent=2)

print(f"[✓] Saved {len(bones_dict)} bones to {out_path}")
