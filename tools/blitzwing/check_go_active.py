import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

for pid in (2253746314803153576, 7609395052744691237, -2446282080136274639, -2922891105374208445):
    go = obj_map[pid].read_typetree()
    print(f"GO PID {pid}: Name='{go.get('m_Name')}' Active={go.get('m_IsActive')}")
