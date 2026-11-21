import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

RAMJET_BUNDLE = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
PROC_BUNDLE = r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle"

for bpath in [RAMJET_BUNDLE, PROC_BUNDLE]:
    print(f"=== Inspecting {bpath} ===")
    env = UnityPy.load(bpath)
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            data = obj.read()
            name = getattr(data, "m_Name", "")
            if any(k in name.lower() for k in ["ramjet", "jet", "vehicle", "transformed", "starscream", "windblade", "cyclonus"]):
                print(f"  AnimationClip: {name}")
