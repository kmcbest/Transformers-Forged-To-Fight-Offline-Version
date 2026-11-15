import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")

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
                for ev in events:
                    print(f"  f={ev.get('f')} d={ev.get('d')}: type={ev.get('type')}")
                    for k, v in ev.items():
                        if k not in ('f', 'd', 'type'):
                            print(f"      {k}: {v}")
