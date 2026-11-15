import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

moves_path = Path("e:/Agent/TFTF-blender/assets_redeco/moves.assetbundle")
env = UnityPy.load(str(moves_path))
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if tt.get("_name") == "move_heavy_ramjet_donut":
            for idx, ev in enumerate(tt.get("_events", [])):
                if "Prop" in ev.get("type", ""):
                    print(f"[{idx}] {ev['type']}: {ev}")
