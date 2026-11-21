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
jstr = tt.get("jSONData", "")

import re
for m in re.finditer(r'cha_optimus[a-zA-Z0-9_]*', jstr):
    pos = m.start()
    print(f"Match '{m.group()}': ...{jstr[max(0, pos-40):min(len(jstr), pos+60)]}...")
