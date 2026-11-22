import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(BUNDLE_PATH))

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        clips.append(tt["m_Name"])

print(f"Total AnimationClips in Megatronus bundle: {len(clips)}")
for c in sorted(clips):
    print(" ", c)
