import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = BASE_DIR / r"assets_redeco\tarn_gs.assetbundle"
env_t = UnityPy.load(str(TARN_BUNDLE))

pids = [2557354436057525021, 5167789811273258802]
for o in env_t.objects:
    if o.path_id in pids:
        tt = o.read_typetree()
        print(f"PID={o.path_id} Type={o.type.name} Name={tt.get('m_Name')}")
