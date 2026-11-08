import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        clips.append(data.get("m_Name", ""))

print(f"Total AnimationClips in Grindor bundle: {len(clips)}")
for c in sorted(clips):
    print("  Clip:", c)
