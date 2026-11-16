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

pids = [-6279366039072279241, 6445516435771417234]
for o in env_b.objects:
    if o.path_id in pids:
        tt = o.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        print(f"PID={o.path_id} Type={o.type.name} GO_PID={go_pid}")

# Also find the GO name
go_pids = []
for o in env_b.objects:
    if o.path_id in pids:
        tt = o.read_typetree()
        go_pids.append(tt.get("m_GameObject", {}).get("m_PathID"))

for o in env_b.objects:
    if o.path_id in go_pids:
        tt = o.read_typetree()
        print(f"GO PID={o.path_id} Name={tt.get('m_Name')}")
