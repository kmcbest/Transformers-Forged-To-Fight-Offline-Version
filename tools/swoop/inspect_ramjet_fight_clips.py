import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController" and obj.path_id == 6432204470035570307:
        d = obj.read_typetree()
        for i, clip in enumerate(d.get("m_Clips", [])):
            orig = clip.get("m_OriginalClip", {}).get("m_PathID")
            over = clip.get("m_OverrideClip", {}).get("m_PathID")
            orig_obj = obj_map.get(orig)
            orig_name = orig_obj.read_typetree().get("m_Name", "") if orig_obj else ""
            over_obj = obj_map.get(over)
            over_name = over_obj.read_typetree().get("m_Name", "") if over_obj else ""
            print(f"  [{i:2d}] orig={orig_name:30s} ({orig}) -> over={over_name} ({over})")
