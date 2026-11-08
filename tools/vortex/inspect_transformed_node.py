import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

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

for tr_id, tree in tr_dict.items():
    go_name = go_dict.get(tr_to_go.get(tr_id), "")
    if go_name == "transformed":
        rot = tree.get("m_LocalRotation")
        pos = tree.get("m_LocalPosition")
        scale = tree.get("m_LocalScale")
        print(f"'transformed' LocalRotation={rot}, LocalPosition={pos}, LocalScale={scale}")
        # also print its father
        father_id = tree.get("m_Father", {}).get("m_PathID")
        father_name = go_dict.get(tr_to_go.get(father_id), "none")
        print(f"Father of transformed is '{father_name}'")
