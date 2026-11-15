import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

rj_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
if not rj_bundle.exists():
    rj_bundle = Path(r"E:\Agent\TFTF-blender\assets_netflix\ramjet_gs_deluxe2008.assetbundle")

print("Loading", rj_bundle)
env = UnityPy.load(str(rj_bundle))

for o in env.objects:
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"Ramjet AOC PID {o.path_id}: name={tt.get('m_Name')}")
        print(f"  BaseController: {tt.get('m_Controller')}")
        for c in tt.get("m_Clips", []):
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            if orig.get("m_PathID") == -7632205551962568777:
                print(f"  Found HeavyAttack: orig={orig} -> over={over}")
