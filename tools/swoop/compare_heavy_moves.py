import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
if not MOVES_BUNDLE.exists():
    MOVES_BUNDLE = Path(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")

env_moves = UnityPy.load(str(MOVES_BUNDLE))

def analyze_move(name_target):
    for obj in env_moves.objects:
        if obj.type.name == "TextAsset":
            d = obj.read_typetree()
            name = d.get("m_Name", "") or ""
            if name == name_target:
                script = d.get("m_Script", "")
                parsed = json.loads(script)
                m = parsed.get("moves", {})
                print(f"=== Move: {m.get('id')} ===")
                events = m.get("events", [])
                for ev in events:
                    etype = ev.get("type")
                    frame = ev.get("f")
                    dur = ev.get("d")
                    # print details for projectile, animation, fx, sound
                    details = {}
                    for k in ["an", "pn", "sn", "fxn", "eid", "ln", "nn", "bn", "tn", "fl"]:
                        if k in ev:
                            details[k] = ev[k]
                    print(f"  f={frame:2d} d={dur:2d} | type={etype:25s} | {details}")

print("--- Grimlock Heavy ---")
analyze_move("move_heavy_grimlock")

print("\n--- Ramjet Heavy ---")
analyze_move("move_heavy_ramjet")
