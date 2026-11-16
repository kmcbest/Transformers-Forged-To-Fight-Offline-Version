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

pids = [-711461190434454571, 548443518610353992, -1815031669912917614, -7538360293670270481]
for o in env_b.objects:
    if o.path_id in pids:
        tt = o.read_typetree()
        print(f"PID={o.path_id} Type={o.type.name} Name={tt.get('m_Name')}")
