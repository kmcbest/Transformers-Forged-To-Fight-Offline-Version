import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Animator":
        data = obj.read_typetree()
        go_ref = data.get("m_GameObject")
        go_name = ""
        if go_ref and go_ref["m_PathID"] != 0:
            go = obj.assets_file.objects[go_ref["m_PathID"]].read_typetree()
            go_name = go.get("m_Name")
        avatar_ref = data.get("m_Avatar")
        av_name = ""
        if avatar_ref and avatar_ref["m_PathID"] != 0:
            av = obj.assets_file.objects[avatar_ref["m_PathID"]].read_typetree()
            av_name = av.get("m_Name")
        print(f"Animator on '{go_name}': avatar='{av_name}' (pathID={avatar_ref.get('m_PathID') if avatar_ref else None})")
