import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

menv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
for o in menv.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if d.m_Name in ("move_heavy_starscream_shoot", "move_heavy_jetfire_shoot", "move_heavy_ramjet_donut", "move_heavy_grimlock", "move_heavy_swoop"):
            evs = json.loads(d.m_Script)["moves"]["events"]
            print(f"\n=== {d.m_Name} ({len(evs)} events) ===")
            for ev in evs:
                t = ev.get("type")
                rest = {k: v for k, v in ev.items() if k not in ("sc", "cc", "dn", "mn", "id", "c", "type", "tar", "inf")}
                print(f"  f={ev.get('f'):2d} d={ev.get('d',0):2d} {t:30s} {rest}")
