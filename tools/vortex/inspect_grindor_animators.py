import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

names = {}
for obj in env.objects:
    if obj.type.name in ["GameObject", "Avatar", "AnimatorController", "AnimatorOverrideController", "MonoBehaviour"]:
        data = obj.read_typetree()
        n = data.get("m_Name", "")
        names[obj.path_id] = (obj.type.name, n)

for obj in env.objects:
    if obj.type.name == "Animator":
        data = obj.read_typetree()
        go_id = data.get("m_GameObject", {}).get("m_PathID")
        ctrl_id = data.get("m_Controller", {}).get("m_PathID")
        av_id = data.get("m_Avatar", {}).get("m_PathID")
        go_info = names.get(go_id, ("?", "?"))
        ctrl_info = names.get(ctrl_id, ("?", "?"))
        av_info = names.get(av_id, ("?", "?"))
        print(f"Animator on GO '{go_info[1]}' (PID {go_id}):")
        print(f"   Controller: {ctrl_info[0]} '{ctrl_info[1]}' (PID {ctrl_id})")
        print(f"   Avatar:     {av_info[0]} '{av_info[1]}' (PID {av_id})")
