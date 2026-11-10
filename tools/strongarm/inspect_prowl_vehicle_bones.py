import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(p_prowl))

id_to_name = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        id_to_name[obj.path_id] = tree.get("m_Name", "")

tr_to_go = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        tree = obj.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        tr_to_go[obj.path_id] = id_to_name.get(go_pid, f"GO_{go_pid}")

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        bones = tree.get("m_Bones", [])
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        smr_go_name = id_to_name.get(go_pid, "")
        if len(bones) == 26:
            print(f"\nVehicle SMR: {smr_go_name} (Bones: {len(bones)})")
            bone_names = [tr_to_go.get(b.get("m_PathID", 0), f"PID_{b.get('m_PathID', 0)}") for b in bones]
            for i, bn in enumerate(bone_names):
                print(f"  [{i}] {bn}")
            root_pid = tree.get("m_RootBone", {}).get("m_PathID", 0)
            print("  RootBone:", tr_to_go.get(root_pid, f"PID_{root_pid}"))
            break
