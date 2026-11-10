import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'm_Name', getattr(data, 'name', ''))
        clips.append(name)

print(f"Total AnimationClips in prowl bundle: {len(clips)}")
for c in sorted(clips):
    if any(k in c.lower() for k in ["vehicle", "victory", "heavy", "idle"]):
        print(f"  {c}")
