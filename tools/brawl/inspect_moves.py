import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

anim_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(anim_path))

clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        name = tt.get('m_Name', '')
        clips.append(name)

targets = ["idle", "jab", "punch", "kick", "frontkick", "special", "victory", "attacklight", "heavy", "vehicle", "optimus"]
found = {}
for t in targets:
    found[t] = [c for c in clips if t in c.lower()]
    print(f"Target '{t}': {len(found[t])} clips found. Sample: {found[t][:5]}")
