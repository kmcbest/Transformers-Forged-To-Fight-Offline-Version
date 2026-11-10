import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import UnityPy

moves_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
if not moves_path.exists():
    moves_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\characters\moves.assetbundle")

print(f"Reading moves bundle: {moves_path}")
env = UnityPy.load(str(moves_path))

prowl_clips = []
ultram_clips = []

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = data.m_Name
        if "prowl" in name.lower():
            prowl_clips.append(name)
        if "ultram" in name.lower() and ("win" in name.lower() or "victory" in name.lower() or "exit" in name.lower() or "celebrate" in name.lower()):
            ultram_clips.append(name)

print(f"\n--- Prowl Clips in moves.assetbundle ({len(prowl_clips)}) ---")
for c in prowl_clips:
    print("  ", c)

print(f"\n--- Ultra Magnus Victory / Win Clips ({len(ultram_clips)}) ---")
for c in ultram_clips:
    print("  ", c)
