import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
proc_bundle = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env_proc = UnityPy.load(str(proc_bundle)) if proc_bundle.exists() else None
proc_map = {o.path_id: o for o in env_proc.objects} if env_proc else {}

obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController" and obj.path_id == -6340484879223379266:
        d = obj.read_typetree()
        print(f"AOC: {d.get('m_Name')}")
        for i, clip in enumerate(d.get("m_Clips", [])):
            orig = clip.get("m_OriginalClip", {}).get("m_PathID")
            over = clip.get("m_OverrideClip", {}).get("m_PathID")
            fid = clip.get("m_OverrideClip", {}).get("m_FileID")
            orig_name = ""
            over_name = ""
            if orig in obj_map:
                orig_name = obj_map[orig].read_typetree().get("m_Name", "")
            elif orig in proc_map:
                orig_name = proc_map[orig].read_typetree().get("m_Name", "")
            if over in obj_map:
                over_name = obj_map[over].read_typetree().get("m_Name", "")
            elif over in proc_map:
                over_name = proc_map[over].read_typetree().get("m_Name", "")
            print(f"  Slot {i:2d}: orig={orig_name} ({orig}) -> over={over_name} (fid={fid}, pid={over})")
