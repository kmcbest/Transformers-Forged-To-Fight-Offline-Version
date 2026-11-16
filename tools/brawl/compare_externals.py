import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
brawl_b = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
meg_b = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"

for path, label in [(brawl_b, "Brawl"), (meg_b, "Megatron")]:
    env = UnityPy.load(str(path))
    sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
    print(f"[{label}] Externals:")
    for i, ext in enumerate(sf.externals):
        print(f"  {i+1}: name={getattr(ext, 'name', None)}, path={getattr(ext, 'path', None)}, guid={getattr(ext, 'guid', None)}")
