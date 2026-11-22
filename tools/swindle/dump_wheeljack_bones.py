import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy
import numpy as np

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\wheeljack_gs_mp20_odr\wheeljack_gs_mp20.assetbundle")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Swindle\00_donor_reference")
OUT_DIR.mkdir(parents=True, exist_ok=True)

env = UnityPy.load(str(BUNDLE_PATH))
obj_map = {o.path_id: o for o in env.objects}

ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
ab_tt = ab_objs[0].read_typetree()

print("AssetBundle Containers:")
for k, v in ab_tt["m_Container"]:
    print(f"  {k} -> {v['asset']['m_PathID']}")

# Find robot and vehicle SMRs
robot_smr = None
veh_smr = None
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt["m_Mesh"]["m_PathID"]
        if mesh_pid in obj_map:
            m_name = obj_map[mesh_pid].read_typetree()["m_Name"]
            if m_name == "cha_wheeljack_gs_mp20_00" and tt.get("m_Enabled", True):
                robot_smr = tt
            elif m_name == "cha_wheeljack_gs_mp20_01":
                veh_smr = tt

print(f"Robot SMR bones count: {len(robot_smr['m_Bones'])}")
bone_names = []
for b in robot_smr["m_Bones"]:
    b_pid = b["m_PathID"]
    if b_pid in obj_map:
        t_obj = obj_map[b_pid]
        tt = t_obj.read_typetree()
        go_pid = tt["m_GameObject"]["m_PathID"]
        go_name = obj_map[go_pid].read_typetree()["m_Name"]
        bone_names.append(go_name)
    else:
        bone_names.append("MISSING")

print(f"Robot Bones ({len(bone_names)}): {bone_names}")

# Mesh m_BindPose and m_BoneNameHashes
robot_mesh_tt = [o.read_typetree() for o in env.objects if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_wheeljack_gs_mp20_00"][0]

bind_poses = robot_mesh_tt["m_BindPose"]
hashes = robot_mesh_tt["m_BoneNameHashes"]
print(f"BindPoses count: {len(bind_poses)}, Hashes count: {len(hashes)}")

rest_positions = {}
for i, name in enumerate(bone_names):
    bp = bind_poses[i]
    m = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ], dtype=np.float32)
    inv = np.linalg.inv(m)
    pos = inv[:3, 3]
    rest_positions[name] = [float(pos[0]), float(pos[1]), float(pos[2])]
    print(f"  {i:2d} {name:25s}: Unity pos=({pos[0]:8.4f}, {pos[1]:8.4f}, {pos[2]:8.4f})")

hierarchy = {}
for b in robot_smr["m_Bones"]:
    b_pid = b["m_PathID"]
    t_obj = obj_map[b_pid]
    tt = t_obj.read_typetree()
    go_pid = tt["m_GameObject"]["m_PathID"]
    b_name = obj_map[go_pid].read_typetree()["m_Name"]
    parent_pid = tt["m_Father"]["m_PathID"]
    parent_name = None
    if parent_pid in obj_map:
        p_go_pid = obj_map[parent_pid].read_typetree()["m_GameObject"]["m_PathID"]
        parent_name = obj_map[p_go_pid].read_typetree()["m_Name"]
    hierarchy[b_name] = parent_name

summary = {
    "bones": bone_names,
    "hierarchy": hierarchy,
    "rest_positions": rest_positions,
    "bone_name_hashes": hashes,
}

with open(OUT_DIR / "wheeljack_donor_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\nSaved donor summary to wheeljack_donor_summary.json!")
