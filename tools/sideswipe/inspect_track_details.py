import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf = list(env.assets)[0]

mdata = sf.objects[8781936353626196161]
tt = mdata.read_typetree()
jdata = json.loads(tt.get("jSONData", "{}"))
tracks = jdata.get("TRACKS", {})

for tid in ("track_29", "track_6"):
    tr = tracks.get(tid, {})
    print(f"\n=== {tid} ===")
    for k, v in tr.items():
        print(f"  {k}: {str(v)[:150]}")
