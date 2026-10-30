import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        t = obj.read_typetree()
        cname = t.get("m_Name")
        clips.append(cname)

print(f"Found {len(clips)} AnimationClips in Arcee bundle:")
for c in clips:
    print(" ", c)
