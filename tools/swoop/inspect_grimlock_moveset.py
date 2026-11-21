import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            d = obj.read_typetree()
            if "_moves" in d:
                moves = d.get("_moves", [])
                for i, m in enumerate(moves):
                    an = m.get("_animStateName", "")
                    mn = m.get("_name", "")
                    if "heavy" in mn.lower() or "heavy" in an.lower():
                        print(f"Grimlock MoveSet Slot {i}: {an} -> {mn} (Asset: {m.get('_asset')})")
        except:
            pass
    elif obj.type.name == "AnimatorOverrideController":
        d = obj.read_typetree()
        print("AnimatorOverrideController:", d.get("m_Name"))
        for clip in d.get("m_Clips", []):
            orig = clip.get("m_OriginalClip", {}).get("m_PathID")
            over = clip.get("m_OverrideClip", {}).get("m_PathID")
            orig_obj = obj_map.get(orig)
            orig_name = orig_obj.read_typetree().get("m_Name", "") if orig_obj else ""
            over_obj = obj_map.get(over)
            over_name = over_obj.read_typetree().get("m_Name", "") if over_obj else ""
            if "heavy" in orig_name.lower() or "heavy" in over_name.lower():
                print(f"  Clip slot: orig={orig_name} ({orig}) -> over={over_name} ({over})")
