import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json, UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
for obj in env.objects:
    if obj.type.name == "TextAsset":
        d = obj.read()
        if getattr(d, "m_Name", "") == "move_heavy_ramjet_donut":
            raw = getattr(d, "m_Script", b"")
            content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            data = json.loads(content)
            events = data.get("moves", {}).get("events", [])
            print(f"Total events in move_heavy_ramjet_donut: {len(events)}")
            for i, ev in enumerate(events):
                print(f"[{i}] f={ev.get('f')} d={ev.get('d')}: type={ev.get('type')}")
                if ev.get("type") == "SlideMoveEvent":
                    print("   SlideMoveEvent:", ev)
                if ev.get("type") == "HitMoveEvent":
                    print("   HitMoveEvent:", ev)
