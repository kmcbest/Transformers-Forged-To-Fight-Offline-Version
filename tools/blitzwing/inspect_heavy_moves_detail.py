import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
moves_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "moves_odr" / "moves.assetbundle"
if not moves_bundle.exists():
    moves_bundle = ROOT / "assets_redeco" / "moves.assetbundle"

print("Moves bundle:", moves_bundle)
env = UnityPy.load(str(moves_bundle))
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        try:
            d = o.read_typetree()
            mname = d.get("m_Name", "")
            if mname in ("move_heavy_ramjet_donut", "move_heavy_megatron_gs_shoot"):
                print(f"\n=== Move: {mname} ===")
                events = d.get("_events", [])
                for ev in events:
                    ev_type = ev.get("type", ev.get("$type", ""))
                    print(f"  Event: type={ev_type}, name={ev.get('name')}, propName={ev.get('propName')}, clipName={ev.get('clipName')}")
        except Exception:
            pass
