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

for obj in env_moves.objects:
    if obj.type.name == "TextAsset":
        d = obj.read_typetree()
        name = d.get("m_Name", "") or ""
        if name == "move_heavy_ramjet_donut":
            print(f"Found {name} (PID: {obj.path_id})")
            parsed = json.loads(d["m_Script"])
            events = parsed["moves"]["events"]
            for ev in events:
                etype = ev.get("type")
                frame = ev.get("f")
                dur = ev.get("d")
                print(f"  f={frame:2d} d={dur:2d} | type={etype:25s} | {ev.get('pn', '')} {ev.get('sn', '')} {ev.get('an', '')}")
            break
