import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import numpy as np
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
OUT_DIR = ROOT / "tools" / "blitzwing"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== Loading {MEG_BUNDLE} ===")
env = UnityPy.load(str(MEG_BUNDLE))

# 1. Map PathID to GameObject and Transform
go_names = {}
transforms = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        d = obj.read()
        go_names[obj.path_id] = d.m_Name
    elif obj.type.name == "Transform":
        t = obj.read_typetree()
        transforms[obj.path_id] = t

# Map Transform PathID -> GameObject Name
tr_to_name = {}
for tr_id, tr in transforms.items():
    go_id = tr.get("m_GameObject", {}).get("m_PathID")
    tr_to_name[tr_id] = go_names.get(go_id, f"Unknown_{go_id}")

# 2. Find Humanoid SMR (51 bones)
humanoid_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        if len(tree.get("m_Bones", [])) == 51:
            humanoid_smr = tree
            break

if not humanoid_smr:
    print("ERROR: Could not find 51-bone Humanoid SMR in Megatron bundle!")
    sys.exit(1)

bone_pids = [b["m_PathID"] for b in humanoid_smr["m_Bones"]]
bone_names = [tr_to_name.get(pid, f"Bone_{idx}") for idx, pid in enumerate(bone_pids)]
print(f"Found 51 humanoid bones: {bone_names}")

# 3. Find Mesh m_BindPose
mesh_pid = humanoid_smr["m_Mesh"]["m_PathID"]
mesh_obj = [o for o in env.objects if o.path_id == mesh_pid][0]
mesh_tree = mesh_obj.read_typetree()
bind_poses = mesh_tree.get("m_BindPose", [])
print(f"Mesh '{mesh_tree.get('m_Name')}' has {len(bind_poses)} bindposes")

# 4. Extract Bone hierarchy & Inverted BindPose positions (World Rest Position of each bone in Unity)
bones_info = {}
for idx, (bname, pid) in enumerate(zip(bone_names, bone_pids)):
    bp = bind_poses[idx]
    # In Unity: m_BindPose is a 4x4 matrix that transforms from world to bone space (inv(WorldMatrix))
    # Its inverse is the WorldMatrix of the bone in Rest Pose!
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv_mat = np.linalg.inv(mat)
    pos = inv_mat[:3, 3].tolist()
    
    # Also find parent transform
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

output_data = {
    "bone_count": len(bone_names),
    "bone_names": bone_names,
    "bones": bones_info,
    "local_aabb": mesh_tree.get("m_LocalAABB", {}),
    "mesh_name": mesh_tree.get("m_Name", "")
}

out_file = OUT_DIR / "megatron_51_authoritative_bindposes.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2)

print(f"[✓] Successfully wrote {out_file} (51 bones)")

# 5. Extract Tank SMR (21 bones)
tank_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        if len(tree.get("m_Bones", [])) == 21:
            tank_smr = tree
            break

if tank_smr:
    tank_bone_pids = [b["m_PathID"] for b in tank_smr["m_Bones"]]
    tank_bone_names = [tr_to_name.get(pid, f"TankBone_{idx}") for idx, pid in enumerate(tank_bone_pids)]
    tank_mesh_pid = tank_smr["m_Mesh"]["m_PathID"]
    tank_mesh_obj = [o for o in env.objects if o.path_id == tank_mesh_pid][0]
    tank_mesh_tree = tank_mesh_obj.read_typetree()
    tank_bp = tank_mesh_tree.get("m_BindPose", [])
    
    tank_bones_info = {}
    for idx, (bname, pid) in enumerate(zip(tank_bone_names, tank_bone_pids)):
        bp = tank_bp[idx]
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
        tank_bones_info[bname] = {
            "index": idx,
            "path_id": pid,
            "parent": parent_name,
            "unity_world_pos": pos,
            "bind_pose_matrix": {f"e{r}{c}": float(bp[f"e{r}{c}"]) for r in range(4) for c in range(4)}
        }
    
    tank_output = {
        "bone_count": len(tank_bone_names),
        "bone_names": tank_bone_names,
        "bones": tank_bones_info,
        "local_aabb": tank_mesh_tree.get("m_LocalAABB", {}),
        "mesh_name": tank_mesh_tree.get("m_Name", "")
    }
    tank_out_file = OUT_DIR / "megatron_tank_21_authoritative_bindposes.json"
    with open(tank_out_file, "w", encoding="utf-8") as f:
        json.dump(tank_output, f, indent=2)
    print(f"[✓] Successfully wrote {tank_out_file} (21 tank bones)")
