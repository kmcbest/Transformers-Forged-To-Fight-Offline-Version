import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

env = UnityPy.load(str(arcee_bundle_path))

go_dict = {}
tr_dict = {}
tr_to_go = {}
go_to_tr = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        go_id = tr.get("m_GameObject", {}).get("m_PathID")
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

print(f"Total GameObjects: {len(go_dict)}, Transforms: {len(tr_dict)}")

# Find root GameObjects (Transforms with no parent)
root_gos = []
for tr_id, tr in tr_dict.items():
    p = tr.get("m_Father", {}).get("m_PathID")
    if p == 0:
        go_id = tr_to_go.get(tr_id)
        go_name = go_dict.get(go_id, {}).get("m_Name")
        root_gos.append((go_name, go_id, tr_id))

print("\nRoot Transforms (no father):")
for name, go_id, tr_id in root_gos:
    print(f"  GO '{name}' (PID: {go_id}) -> TR PID: {tr_id}")

# Check body SMRs
print("\nBody SMRs:")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_id = tree.get("m_Mesh", {}).get("m_PathID")
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        go_name = go_dict.get(go_id, {}).get("m_Name")
        bones = tree.get("m_Bones", [])
        if len(bones) == 63:
            print(f"  SMR PID: {obj.path_id} on GO '{go_name}' (PID: {go_id}) has {len(bones)} bones")
            sample_bone_names = []
            for b in bones[:5]:
                b_tr = b.get("m_PathID")
                b_go = tr_to_go.get(b_tr)
                sample_bone_names.append(go_dict.get(b_go, {}).get("m_Name"))
            print(f"    Sample bones: {sample_bone_names}")
