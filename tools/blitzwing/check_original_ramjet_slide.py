import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json, UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")
for obj in env.objects:
    if obj.type.name == "TextAsset":
        d = obj.read()
        if getattr(d, "m_Name", "") == "move_heavy_ramjet_donut":
            raw = getattr(d, "m_Script", b"")
            content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            data = json.loads(content)
            events = data.get("moves", {}).get("events", [])
            for i, ev in enumerate(events):
                if ev.get("type") in ("SlideMoveEvent", "HitMoveEvent"):
                    print(f"Original [{i:2d}] {ev['type']}: {ev}")
