import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(p_prowl))

id_to_name = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        id_to_name[obj.path_id] = tree.get("m_Name", "")

tr_nodes = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        tree = obj.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        tr_nodes[obj.path_id] = {
            "name": id_to_name.get(go_pid, ""),
            "pos": tree.get("m_LocalPosition", {}),
            "rot": tree.get("m_LocalRotation", {}),
            "scale": tree.get("m_LocalScale", {}),
            "parent": tree.get("m_Father", {}).get("m_PathID", 0),
            "children": [c.get("m_PathID", 0) for c in tree.get("m_Children", [])]
        }

# Find cha_prowl_gs_deluxe2016_00 SMR
smr_00 = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        if id_to_name.get(go_pid, "") == "cha_prowl_gs_deluxe2016_00":
            smr_00 = tree
            break

# Find Mesh 00 bindposes
mesh_00 = None
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name", "") == "cha_prowl_gs_deluxe2016_00":
            mesh_00 = tree
            break

print(f"Found SMR 00: {smr_00 is not None}, Mesh 00: {mesh_00 is not None}")

bones_data = []
if smr_00 and mesh_00:
    smr_bones = smr_00.get("m_Bones", [])
    bindposes = mesh_00.get("m_BindPose", [])
    hashes = mesh_00.get("m_BoneNameHashes", [])
    print(f"SMR Bones: {len(smr_bones)}, BindPoses: {len(bindposes)}, Hashes: {len(hashes)}")
    
    for i, b_ptr in enumerate(smr_bones):
        pid = b_ptr.get("m_PathID", 0)
        tr = tr_nodes.get(pid, {})
        b_name = tr.get("name", f"Bone_{i}")
        bp = bindposes[i] if i < len(bindposes) else None
        h = hashes[i] if i < len(hashes) else None
        bones_data.append({
            "index": i,
            "name": b_name,
            "path_id": pid,
            "hash": h,
            "bindpose": bp,
            "local_pos": tr.get("pos"),
            "local_rot": tr.get("rot"),
            "local_scale": tr.get("scale")
        })

out_json = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(bones_data, f, indent=2)

print(f"Saved {len(bones_data)} Prowl robot bones to {out_json}")
