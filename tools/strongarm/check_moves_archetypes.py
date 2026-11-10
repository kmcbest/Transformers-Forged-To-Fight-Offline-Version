import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import UnityPy

moves_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
env = UnityPy.load(str(moves_path))

all_clip_names = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        all_clip_names.append(obj.read().m_Name)

print(f"Total clips in moves.assetbundle: {len(all_clip_names)}")
for keyword in ["car", "deluxe", "police", "scout", "shotgun", "baton", "ultram"]:
    matches = [c for c in all_clip_names if keyword in c.lower()]
    print(f"Keyword '{keyword}': {len(matches)} matches")
    for m in matches[:5]:
        print(f"   {m}")
