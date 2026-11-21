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
mc = jdata.get("MC", {})
print("MC keys:", list(mc.keys()))
for k, v in mc.items():
    if any(term in str(v) for term in ["cha_optimus", "m_Enabled", "enabled", "29", "track_6", "track_29"]):
        print(f"MC key {k}: {str(v)[:150]}")
