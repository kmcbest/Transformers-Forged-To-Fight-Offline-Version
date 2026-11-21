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
        if name == "move_heavy_grimlock":
            script = d.get("m_Script", "")
            print(f"=== {name} ===")
            print(script[:2000])
            try:
                parsed = json.loads(script)
                print("\nKeys in move_heavy_grimlock:", list(parsed.keys()))
                if "animation" in parsed:
                    print("animation:", parsed["animation"])
                if "projectiles" in parsed:
                    print("projectiles:", parsed["projectiles"])
                if "events" in parsed:
                    print("events:", parsed["events"][:5])
            except Exception as e:
                print("JSON parse error:", e)
            break
