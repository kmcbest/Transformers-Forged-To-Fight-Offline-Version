import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"

env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

matinee_obj = sf.objects[8781936353626196161]
tt = matinee_obj.read_typetree()
jstr = tt.get("jSONData", "")

import re
matches = [m.start() for m in re.finditer(r'optimus', jstr, re.IGNORECASE)]
for idx, pos in enumerate(matches):
    start = max(0, pos - 60)
    end = min(len(jstr), pos + 80)
    print(f"[{idx}] ...{jstr[start:end]}...")
