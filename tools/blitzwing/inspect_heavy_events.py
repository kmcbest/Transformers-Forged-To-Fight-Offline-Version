import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")

for name in ["move_heavy_megatron_gs_shoot", "move_heavy_ramjet_donut"]:
    print(f"\n==================== {name} ====================")
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            if getattr(d, "m_Name", "") == name:
                raw = getattr(d, "m_Script", b"")
                content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
                data = json.loads(content)
                events = data.get("moves", {}).get("events", [])
                print(f"Total events: {len(events)}")
                for ev in events:
                    ev_type = ev.get("type", "")
                    an = ev.get("an", "")
                    dn = ev.get("dn", "")
                    st = ev.get("st", 0)
                    dur = ev.get("dur", 0)
                    clip = ev.get("cl", "")
                    print(f"  [{st:0.2f}s - dur {dur:0.2f}s] {ev_type} | an='{an}' | clip='{clip}' | dn='{dn}'")
