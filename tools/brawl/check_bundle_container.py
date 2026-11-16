import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
env_b = UnityPy.load(str(BRAWL_BUNDLE))

for o in env_b.objects:
    if o.type.name == "AssetBundle":
        tt = o.read_typetree()
        print("AssetBundle Name:", tt.get("m_AssetBundleName"))
        print("Container:")
        for k, v in tt.get("m_Container", []):
            print(f"  {k} -> {v}")
