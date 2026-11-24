import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
cfx_p = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_fx_procedural.assetbundle")
cfx = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_fx.assetbundle")

for label, e in [("cfx", cfx), ("cfx_p", cfx_p)]:
    for o in e.objects:
        if o.type.name == "GameObject":
            nm = o.read_typetree().get("m_Name", "")
            if nm == "fx_l_hit_small_perceptual_orange":
                print(f"Found {nm} in {label}: PID={o.path_id}")

cnt = 0
for o in env.objects:
    if o.type.name == "TextAsset":
        t = o.read()
        if "special" in t.m_Name:
            raw = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", errors="replace")
            if "PropMoveEvent" in raw:
                mv = json.loads(raw)["moves"]
                for ev in mv.get("events", []):
                    if ev.get("type") == "PropMoveEvent":
                        print(f"[{t.m_Name}] {ev}")
                        cnt += 1
                        if cnt >= 8:
                            sys.exit(0)
