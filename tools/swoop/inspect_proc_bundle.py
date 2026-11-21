import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

PROC_PATH = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
if PROC_PATH.exists():
    env = UnityPy.load(str(PROC_PATH))
    clips = []
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            d = obj.read()
            clips.append(d.m_Name)
    print(f"Total clips in character_anim_procedural: {len(clips)}")
    for k in ["brawler", "tactician", "ramjet", "seeker", "attack", "jab", "kick", "victory", "idle"]:
        matches = [c for c in clips if k in c.lower()]
        print(f"  Matches for '{k}': {len(matches)} (e.g. {matches[:3]})")
