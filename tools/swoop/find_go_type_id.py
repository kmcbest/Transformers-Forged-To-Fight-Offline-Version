import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

for tid, t in enumerate(sf.types):
    if t.class_id in [1, 4]: # GameObject (1), Transform (4)
        print(f"class_id={t.class_id} -> type_id={tid}")
