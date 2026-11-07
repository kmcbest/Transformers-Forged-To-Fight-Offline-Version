import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

# 1. Check SP3 & Heavy move events for Movie Ironhide (cin_rotf) in moves.assetbundle
mb = Path(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")
env = UnityPy.load(str(mb))
for obj in env.objects:
    if obj.type.name == "TextAsset":
        d = obj.read()
        nm = getattr(d, "m_Name", "")
        if "ironhide" in nm.lower() and any(k in nm.lower() for k in ["special_03", "heavy", "cin", "rotf"]):
            print(f"\n=== Move: {nm} ===")
            try:
                data = json.loads(d.m_Script)
                events = data.get("moves", {}).get("events", [])
                for ev in events:
                    et = ev.get("type", "")
                    if any(k in str(ev).lower() for k in ["transform", "anim", "vehicle", "visible", "swap", "mesh", "special"]):
                        print(" ", {k: v for k, v in ev.items() if k in ("type", "time", "start", "end", "duration", "clip", "anim", "name", "mn", "show", "enable", "visible", "state") or "time" in k.lower() or "anim" in k.lower() or "trans" in k.lower()})
            except Exception as e:
                print("  parse err:", e)
