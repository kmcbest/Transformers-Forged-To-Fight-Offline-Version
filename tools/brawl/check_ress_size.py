import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"

for bpath, label in [(DONOR_BUNDLE, "Donor"), (BRAWL_BUNDLE, "Brawl")]:
    env = UnityPy.load(str(bpath))
    print(f"[{label}] files in bundle:")
    for k, v in env.file.files.items():
        data_len = len(v.read()) if hasattr(v, 'read') else (len(v.data) if hasattr(v, 'data') else 'N/A')
        print(f"  {k}: size={data_len}")
