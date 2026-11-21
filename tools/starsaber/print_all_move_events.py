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
            ev_type = ev.get("type")
            f = ev.get("f")
            d = ev.get("d")
            p = ev.get("p")
            l = ev.get("l")
            proj = ev.get("proj") or ev.get("pr")
            print(f"[{ev_type}] f={f} d={d} prop={p} loc={l} proj={proj}")
