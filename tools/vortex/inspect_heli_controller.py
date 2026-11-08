import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

clip_names = {}
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        clip_names[obj.path_id] = data.get("m_Name")

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        data = obj.read_typetree()
        if "heli" in data.get("m_Name", "").lower():
            print(f"AnimatorOverrideController: {data.get('m_Name')}")
            for c in data.get("m_Clips", []):
                orig_id = c.get("m_OriginalClip", {}).get("m_PathID")
                over_id = c.get("m_OverrideClip", {}).get("m_PathID")
                orig_name = clip_names.get(orig_id, f"External/Unknown({orig_id})")
                over_name = clip_names.get(over_id, f"External/Unknown({over_id})")
                print(f"  {orig_name} -> {over_name}")
