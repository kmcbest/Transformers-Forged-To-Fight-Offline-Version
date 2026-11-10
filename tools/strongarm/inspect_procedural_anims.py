import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
if p.exists():
    print(f"Inspecting {p.name}...")
    env = UnityPy.load(str(p))
    clips = []
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            d = obj.read()
            name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
            clips.append(name)
    print(f"Found {len(clips)} AnimationClips in character_anim_procedural:")
    for c in sorted(clips)[:20]:
        print(f"  {c}")
else:
    print("character_anim_procedural does not exist")
