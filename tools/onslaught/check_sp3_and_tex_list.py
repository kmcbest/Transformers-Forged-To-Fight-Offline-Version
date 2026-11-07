import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

mb = Path(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")
env = UnityPy.load(str(mb))
for obj in env.objects:
    if obj.type.name == "TextAsset":
        d = obj.read()
        nm = getattr(d, "m_Name", "")
        if "ironhide" in nm.lower():
            print(f"Move asset: {nm}")
            if any(k in nm.lower() for k in ["special", "sp3", "03", "heavy"]):
                data = json.loads(d.m_Script)
                for ev in data.get("moves", {}).get("events", []):
                    et = ev.get("type", "")
                    if any(k in et.lower() for k in ["transform", "anim", "scale", "vis"]):
                        print("  ->", json.dumps(ev, ensure_ascii=False)[:240])

print("\n=== TEXTURE FILES IN 3rd-party-models/onslaught/textures ===")
tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\textures")
for p in sorted(tex_dir.iterdir()):
    print(" ", p.name)
