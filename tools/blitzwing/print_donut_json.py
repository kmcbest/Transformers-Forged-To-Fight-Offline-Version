import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, json

moves_bundle = Path(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")
env = UnityPy.load(str(moves_bundle))

for o in env.objects:
    if o.path_id == -8528702938335562906:
        tt = o.read_typetree()
        script = tt.get("m_Script", "")
        print("move_heavy_ramjet_donut content:")
        # It might be json
        try:
            data = json.loads(script)
            print(json.dumps(data, indent=2))
        except:
            print(script)
