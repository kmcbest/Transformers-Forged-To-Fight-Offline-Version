import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
print(f"Loading {BUNDLE_PATH}...")
env = UnityPy.load(str(BUNDLE_PATH))

counts = {}
clips = []
prefabs = []
materials = []
textures = []

for obj in env.objects:
    t = obj.type.name
    counts[t] = counts.get(t, 0) + 1
    if t == "AnimationClip":
        d = obj.read()
        clips.append(d.m_Name)
    elif t == "GameObject":
        d = obj.read()
        if "ramjet" in d.m_Name.lower():
            prefabs.append(d.m_Name)
    elif t == "Material":
        d = obj.read()
        materials.append(d.m_Name)
    elif t == "Texture2D":
        d = obj.read()
        textures.append(d.m_Name)

print(f"Object counts: {counts}")
print(f"Prefabs: {prefabs[:10]}")
print(f"Materials: {materials}")
print(f"Textures: {textures}")
print(f"Total AnimationClips: {len(clips)}")
print(f"Sample AnimationClips: {clips[:20]}")
for c in clips:
    if any(k in c.lower() for k in ["idle", "attack", "kick", "victory", "vehicle", "transform"]):
        print(f"  Clip: {c}")
