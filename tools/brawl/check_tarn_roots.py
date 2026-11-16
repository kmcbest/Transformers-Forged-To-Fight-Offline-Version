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
        print(f"PID={o.path_id} Type={o.type.name} Root={tt.get('m_RootGameObject')}")
        root_pid = tt.get('m_RootGameObject', {}).get('m_PathID')
        for o2 in env_t.objects:
            if o2.path_id == root_pid:
                tt2 = o2.read_typetree()
                print(f"  Root GO PID={o2.path_id} Name={tt2.get('m_Name')}")
