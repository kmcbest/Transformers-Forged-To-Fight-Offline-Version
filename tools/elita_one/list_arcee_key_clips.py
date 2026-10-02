import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name:
            clips.append(name)

print(f"Total AnimationClips in Arcee bundle: {len(clips)}")
for c in sorted(clips):
    if any(k in c.lower() for k in ["idle", "attack", "special", "victory", "intro", "stun", "block"]):
        print("  -", c)
