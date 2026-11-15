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
    try:
        tt = o.read_typetree()
        name = tt.get("m_Name", "")
        if "donut" in name or "ramjet" in name:
            print(f"Object PID {o.path_id}, type={o.type.name}, name={name}")
    except:
        pass
