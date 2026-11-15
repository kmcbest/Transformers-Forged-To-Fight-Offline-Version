import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        clips.append(getattr(d, "m_Name", ""))

print("Total clips:", len(clips))
for c in sorted(clips):
    print(" ", c)
