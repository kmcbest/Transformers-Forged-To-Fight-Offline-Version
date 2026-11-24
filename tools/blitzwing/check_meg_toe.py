import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import UnityPy

p = Path("extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(p))
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_megatron_gs_leader2015_00":
            b_hashes = tt["m_BoneNameHashes"]
            print("Megatron bone hashes count:", len(b_hashes))
