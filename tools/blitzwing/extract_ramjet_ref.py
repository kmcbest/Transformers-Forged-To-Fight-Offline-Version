import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import numpy as np
import UnityPy

RAMJET_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\tools\blitzwing")

print(f"=== Loading {RAMJET_BUNDLE} ===")
env = UnityPy.load(str(RAMJET_BUNDLE))

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

jet_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        if len(tree.get("m_Bones", [])) == 29:
            jet_smr = tree
            break

if not jet_smr:
    print("ERROR: Could not find 29-bone Jet SMR in Ramjet bundle!")
    sys.exit(1)

jet_bone_pids = [b["m_PathID"] for b in jet_smr["m_Bones"]]
jet_bone_names = [tr_to_name.get(pid, f"JetBone_{idx}") for idx, pid in enumerate(jet_bone_pids)]
jet_mesh_pid = jet_smr["m_Mesh"]["m_PathID"]
jet_mesh_obj = [o for o in env.objects if o.path_id == jet_mesh_pid][0]
jet_mesh_tree = jet_mesh_obj.read_typetree()
jet_bp = jet_mesh_tree.get("m_BindPose", [])

jet_bones_info = {}
for idx, (bname, pid) in enumerate(zip(jet_bone_names, jet_bone_pids)):
    bp = jet_bp[idx]
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
    jet_bones_info[bname] = {
        "index": idx,
        "path_id": pid,
        "parent": parent_name,
        "unity_world_pos": pos,
        "bind_pose_matrix": {f"e{r}{c}": float(bp[f"e{r}{c}"]) for r in range(4) for c in range(4)}
    }

jet_output = {
    "bone_count": len(jet_bone_names),
    "bone_names": jet_bone_names,
    "bones": jet_bones_info,
    "local_aabb": jet_mesh_tree.get("m_LocalAABB", {}),
    "mesh_name": jet_mesh_tree.get("m_Name", "")
}
jet_out_file = OUT_DIR / "ramjet_jet_29_authoritative_bindposes.json"
with open(jet_out_file, "w", encoding="utf-8") as f:
    json.dump(jet_output, f, indent=2)
print(f"[✓] Successfully wrote {jet_out_file} (29 jet bones)")
