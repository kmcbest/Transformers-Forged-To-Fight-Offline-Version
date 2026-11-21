import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

RAMJET_AB = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(RAMJET_AB))
clips = []
for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        clips.append(tt["m_Name"])
print(f"Total clips in Ramjet bundle ({len(clips)}):")
for c in sorted(clips):
    print(f"  {c}")
