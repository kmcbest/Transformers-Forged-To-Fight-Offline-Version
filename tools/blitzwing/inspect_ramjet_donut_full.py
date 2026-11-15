import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

moves_bundle = Path(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")
env = UnityPy.load(str(moves_bundle))

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if tt.get("m_Name") == "move_heavy_ramjet_donut":
            print(f"Found move_heavy_ramjet_donut (PID {o.path_id}):")
            events = tt.get("_events", [])
            for i, ev in enumerate(events):
                print(f"  Event {i}: time={ev.get('_triggerTime')} type={ev.get('_type')} name={ev.get('_name')}")
                for k, v in ev.items():
                    if k not in ("_triggerTime", "_type", "_name"):
                        print(f"    {k}: {v}")
