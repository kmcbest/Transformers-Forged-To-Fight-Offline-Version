import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env_d = UnityPy.load(str(DONOR_BUNDLE))

for o in env_d.objects:
    if o.path_id == -9025351850097636016:
        tt = o.read_typetree()
        hashes = tt.get('m_BoneNameHashes', [])
        print("Donor Vehicle Mesh Hashes count:", len(hashes))
        print("239972378 in hashes:", 239972378 in hashes)
        if 239972378 in hashes:
            print("Index of 239972378:", hashes.index(239972378))
        print("RootBoneNameHash:", tt.get('m_RootBoneNameHash'))
