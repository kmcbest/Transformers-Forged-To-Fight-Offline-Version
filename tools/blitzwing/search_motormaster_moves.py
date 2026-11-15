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
        if "motormaster" in name and "special" in name:
            raw = getattr(d, "m_Script", b"")
            content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            data = json.loads(content)
            events = data.get("moves", {}).get("events", [])
            print(f"\n[{name}]")
            for ev in events:
                if any(k in ev.get("type", "") for k in ("Slide", "Move", "Velocity", "Dash")):
                    print(f"  f={ev.get('f')} d={ev.get('d')}: {ev.get('type')}")
                    for k in ('sd', 'di', 'tt', 'ccs', 'sp', 'target'):
                        if k in ev: print(f"      {k}={ev[k]}")
