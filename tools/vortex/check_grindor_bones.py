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

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        go_name = go_dict.get(go_id)
        bones = tree.get("m_Bones", [])
        if len(bones) == 45:
            bone_names = [go_dict.get(tr_to_go.get(b.get("m_PathID"))) for b in bones]
            root_id = tree.get("m_RootBone", {}).get("m_PathID")
            root_name = go_dict.get(tr_to_go.get(root_id))
            print(f"Vehicle SMR on {go_name}: RootBone={root_name}")
            print(f"Vehicle SMR bones ({len(bone_names)}): {bone_names}")
            break
        elif len(bones) == 78:
            bone_names = [go_dict.get(tr_to_go.get(b.get("m_PathID"))) for b in bones]
            root_id = tree.get("m_RootBone", {}).get("m_PathID")
            root_name = go_dict.get(tr_to_go.get(root_id))
            print(f"Robot SMR on {go_name}: RootBone={root_name}")
            print(f"Robot SMR bones ({len(bone_names)}): {bone_names[:10]}... ({len(bone_names)} total)")
