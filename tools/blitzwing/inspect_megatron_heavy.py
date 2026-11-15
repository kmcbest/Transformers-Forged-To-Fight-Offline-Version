import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/moves.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            data = obj.read()
            if getattr(data, "name", "") == "move_heavy_megatron_gs_shoot":
                tt = obj.read_typetree()
                print("Found move_heavy_megatron_gs_shoot:")
                events = tt.get("_events", [])
                for ev in events:
                    ev_type = ev.get("$type", "") or ev.get("m_Type", "")
                    name = ev.get("_name", "")
                    frame = ev.get("_frame", "")
                    print(f"  Frame {frame}: type={ev_type} name={name}")
        except Exception as e:
            pass
