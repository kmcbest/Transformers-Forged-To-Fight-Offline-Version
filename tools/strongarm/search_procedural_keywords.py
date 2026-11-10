import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(p))

clips = {}
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        clips[name] = obj.path_id

print(f"Total clips: {len(clips)}")
for kw in ["prowl", "car", "deluxe", "shotgun", "baton", "chain", "ultram"]:
    matches = [c for c in clips.keys() if kw in c.lower()]
    print(f"\nKeyword '{kw}': {len(matches)} matches")
    for m in sorted(matches):
        print(f"   {m} (PID={clips[m]})")
