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

# Find MatineeData in cloned stage
OP_MATINEE_DATA_PID = 8781936353626196161
mdata = sf.objects.get(OP_MATINEE_DATA_PID)
if mdata:
    tt = mdata.read_typetree()
    jdata = json.loads(tt.get("jSONData", "{}"))
    tracks = jdata.get("TRACKS", {})
    print(f"Total tracks in cloned Optimus MatineeData: {len(tracks)}")
    for k, v in tracks.items():
        if isinstance(v, dict) and "eid" in v:
            print(f"  {k}: en={v.get('en')!r}, enp={v.get('enp')!r}, eid={v.get('eid')!r}")
