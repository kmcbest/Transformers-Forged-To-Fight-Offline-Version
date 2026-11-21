import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy

BUNDLE_PATH = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle"
env = UnityPy.load(BUNDLE_PATH)

clips = []
for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        cname = tt.get("m_Name", "")
        dur = tt.get("m_MuscleClip", {}).get("m_StopTime", 0.0)
        clips.append((cname, dur))

print(f"Barricade bundle has {len(clips)} AnimationClips:")
for name, dur in sorted(clips):
    print(f"  {name:40s} (dur={dur:.2f}s)")
