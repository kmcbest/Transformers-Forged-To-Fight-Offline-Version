import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

gos = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        gos[obj.path_id] = obj.read_typetree().get("m_Name")

for obj in env.objects:
    if obj.type.name == "Transform":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        go_name = gos.get(go_id, "")
        if go_name == "RotorMain":
            print(f"RotorMain Transform (PID {obj.path_id}):")
            print(f"  LocalPos: {tree.get('m_LocalPosition')}")
            print(f"  LocalRot: {tree.get('m_LocalRotation')}")
            print(f"  LocalScale: {tree.get('m_LocalScale')}")
            # check parent
            father_id = tree.get("m_Father", {}).get("m_PathID")
            print(f"  Parent Transform PID: {father_id}")
