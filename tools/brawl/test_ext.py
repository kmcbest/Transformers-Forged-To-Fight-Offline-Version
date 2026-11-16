import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

env = UnityPy.load(str(MEG_BUNDLE))
sf = list(env.assets)[0]
ext = sf.externals[0]
print(dir(ext))
for attr in dir(ext):
    if not attr.startswith("__"):
        print(attr, getattr(ext, attr))
