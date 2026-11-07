import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")
id_to_obj = {o.path_id: o for o in env.objects}

def get_name(pid):
    o = id_to_obj.get(pid)
    if not o:
        return "None"
    return o.read_typetree().get("m_Name", "")

print("=== ALL ANIMATORS IN IRONHIDE BUNDLE ===")
for o in env.objects:
    if o.type.name == "Animator":
        t = o.read_typetree()
        go_pid = t["m_GameObject"]["m_PathID"]
        av_pid = t["m_Avatar"]["m_PathID"]
        ctrl_pid = t["m_Controller"]["m_PathID"]
        print(f"Animator on GO '{get_name(go_pid)}' (go_pid={go_pid}): avatar='{get_name(av_pid)}' (av_pid={av_pid}), ctrl='{get_name(ctrl_pid)}', hasTransformHierarchy={t.get('m_HasTransformHierarchy')}")

print("\n=== ALL AVATARS IN IRONHIDE BUNDLE ===")
for o in env.objects:
    if o.type.name == "Avatar":
        t = o.read_typetree()
        tos = t.get("m_TOS", [])
        print(f"Avatar '{t.get('m_Name')}' (pid={o.path_id}): avatarSize={t.get('m_AvatarSize')}, TOS count={len(tos)}")
        for item in tos[:8]:
            print(f"    TOS: {item}")
