import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            print("Found cha_grindor_cin_rotf_01!")
            # Get bone names and their bindposes or check bone positions
            # Let's inspect bone transforms in the prefab!
            break

# In the prefab, let's inspect the positions of RotorMain, Tail, BodyHeadRight, BodyHeadLeft
go_dict = {}
tr_dict = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree().get("m_Name")
    elif obj.type.name == "Transform":
        tree = obj.read_typetree()
        tr_dict[obj.path_id] = tree
        tr_to_go[obj.path_id] = tree.get("m_GameObject", {}).get("m_PathID")

print("\n--- Key Vehicle Bone Positions in Grindor Prefab ---")
for tr_id, tree in tr_dict.items():
    go_name = go_dict.get(tr_to_go.get(tr_id), "")
    if any(k in go_name for k in ["RotorMain", "Tail", "BodyHead", "BodyRear", "WingLeft", "WingRight", "Gun", "BodyTop"]):
        pos = tree.get("m_LocalPosition", {})
        print(f"Bone '{go_name}': LocalPos = ({pos.get('x'):.2f}, {pos.get('y'):.2f}, {pos.get('z'):.2f})")
