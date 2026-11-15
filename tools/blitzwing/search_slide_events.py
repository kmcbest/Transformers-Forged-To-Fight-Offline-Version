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
        name = getattr(d, "m_Name", "")
        if "ramjet" in name or "dash" in name:
            raw = getattr(d, "m_Script", b"")
            content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            if "SlideMoveEvent" in content:
                data = json.loads(content)
                events = data.get("moves", {}).get("events", [])
                for ev in events:
                    if ev.get("type") == "SlideMoveEvent":
                        print(f"[{name}] f={ev.get('f')} d={ev.get('d')}: sd={ev.get('sd')} di={ev.get('di')} tt={ev.get('tt')} ccs={ev.get('ccs')}")
