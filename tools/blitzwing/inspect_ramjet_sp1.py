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
        if name == "move_ramjet_special_01":
            raw = getattr(d, "m_Script", b"")
            content = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            data = json.loads(content)
            events = data.get("moves", {}).get("events", [])
            for ev in events:
                print(f"[{name}] f={ev.get('f')} d={ev.get('d')}: type={ev.get('type')}")
                if "Move" in ev.get("type", ""):
                    for k in ('sd', 'di', 'tt', 'ccs', 'sp', 'target'):
                        if k in ev: print(f"    {k}={ev[k]}")
