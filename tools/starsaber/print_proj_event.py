import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import json

moves_path = r"E:\Agent\TFTF\assets_netflix\moves.assetbundle"
env = UnityPy.load(moves_path)

for obj in env.objects:
    if obj.path_id == 6811001981586741581:
        tree = obj.read_typetree()
        parsed = json.loads(tree.get("m_Script", "{}"))
        for ev in parsed.get("moves", {}).get("events", []):
            if ev.get("type") in ("ProjectileMoveEvent", "ParticleMoveEvent"):
                print(f"=== {ev.get('type')} ===")
                print(json.dumps(ev, indent=2))
