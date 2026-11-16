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
    print(f"[{label}] Objects with StreamData:")
    for o in env.objects:
        try:
            tt = o.read_typetree()
            for k in ("m_StreamData", "_streamData"):
                if k in tt and isinstance(tt[k], dict):
                    sd = tt[k]
                    if sd.get("size", 0) > 0 or sd.get("path"):
                        print(f"  PID={o.path_id} Type={o.type.name} Name={tt.get('m_Name')} Path={sd.get('path')} Offset={sd.get('offset')} Size={sd.get('size')}")
        except:
            pass
