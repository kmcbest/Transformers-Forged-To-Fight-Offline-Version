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

for tid in ("track_29", "track_6", "track_5", "track_27", "track_28", "track_7", "track_8"):
    if tid in tracks:
        tr = tracks[tid]
        print(f"\n{tid}: en={tr.get('en')}, enp={tr.get('enp')}, eid={tr.get('eid')}")
        # check event containers
        ec_count = tracks.get(f"{tid}_econtainer_count", 0)
        print(f"  event containers count: {ec_count}")
        for i in range(ec_count):
            ec = tracks.get(f"{tid}_econtainer_{i}", {})
            print(f"    ec_{i}: {ec}")
