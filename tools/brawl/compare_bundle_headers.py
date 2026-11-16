import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
tarn_b = BASE_DIR / r"assets_redeco\tarn_gs.assetbundle"
bw_b = BASE_DIR / r"assets_redeco\blitzwing_gs.assetbundle"
brawl_b = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
meg_b = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"

for path, label in [(tarn_b, "Tarn"), (bw_b, "Blitzwing"), (brawl_b, "Brawl"), (meg_b, "Megatron")]:
    if path.exists():
        env = UnityPy.load(str(path))
        print(f"[{label}] File names in bundle:")
        for k, v in env.file.files.items():
            print(f"  key: {k}, type: {type(v).__name__}, name: {getattr(v, 'name', None)}")
        sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]
        print(f"  sf.name: {sf.name}, sf.unity_version: {sf.unity_version}, sf.target_platform: {sf.target_platform}")
        print(f"  objects count: {len(sf.objects)}, types count: {len(sf.types)}")
