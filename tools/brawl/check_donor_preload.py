import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(str(DONOR))

for o in env.objects:
    if o.type.name == "AssetBundle":
        tt = o.read_typetree()
        print("Donor AssetBundle Container:")
        for c in tt.get("m_Container", []):
            print(" ", c)
        print("Donor PreloadTable count:", len(tt.get("m_PreloadTable", [])))
        # Check if preload table matches brawl
