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

env = UnityPy.load(str(BUNDLE_PATH))
obj_map = {o.path_id: o for o in env.objects}

veh_smr = None
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt["m_Mesh"]["m_PathID"]
        if mesh_pid in obj_map:
            m_name = obj_map[mesh_pid].read_typetree()["m_Name"]
            if m_name == "cha_wheeljack_gs_mp20_01":
                veh_smr = tt
                break

print(f"Vehicle SMR bones count: {len(veh_smr['m_Bones'])}")
bone_names = []
for b in veh_smr["m_Bones"]:
    b_pid = b["m_PathID"]
    if b_pid in obj_map:
        t_obj = obj_map[b_pid]
        tt = t_obj.read_typetree()
        go_pid = tt["m_GameObject"]["m_PathID"]
        go_name = obj_map[go_pid].read_typetree()["m_Name"]
        bone_names.append(go_name)
    else:
        bone_names.append("MISSING")

print(f"Vehicle Bones ({len(bone_names)}): {bone_names}")

veh_mesh_tt = [o.read_typetree() for o in env.objects if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_wheeljack_gs_mp20_01"][0]
bind_poses = veh_mesh_tt["m_BindPose"]
hashes = veh_mesh_tt["m_BoneNameHashes"]
print(f"Veh BindPoses: {len(bind_poses)}, Hashes: {len(hashes)}")

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

veh_summary = {
    "bones": bone_names,
    "rest_positions": rest_positions,
    "bone_name_hashes": hashes,
}

with open(OUT_DIR / "wheeljack_veh_donor_summary.json", "w", encoding="utf-8") as f:
    json.dump(veh_summary, f, indent=2)

print("\nSaved veh summary to wheeljack_veh_donor_summary.json!")
