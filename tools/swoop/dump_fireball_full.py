import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

fireball_go = obj_map[5433757232512100521]
print("=== projectile_grimlock_fireball GameObject ===")
print(json.dumps(fireball_go.read_typetree(), indent=2))

for c in fireball_go.read_typetree().get("m_Component", []):
    cid = c.get("component", {}).get("m_PathID")
    c_obj = obj_map.get(cid)
    if c_obj:
        print(f"\n--- Component {c_obj.type.name} (PID: {cid}) ---")
        tt = c_obj.read_typetree()
        print(json.dumps(tt, indent=2))
