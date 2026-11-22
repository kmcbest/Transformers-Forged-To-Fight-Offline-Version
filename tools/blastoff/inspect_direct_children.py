import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blastoff_gs.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

root_tr = obj_map[3076213683770163573].read_typetree()
print("All direct children of Blastoff_GS:")
for c in root_tr.get("m_Children", []):
    ctr = obj_map[c.get("m_PathID")].read_typetree()
    cgo = obj_map[ctr.get("m_GameObject", {}).get("m_PathID")].read_typetree()
    print(f"  - {cgo.get('m_Name')}: scale={ctr.get('m_LocalScale')} pos={ctr.get('m_LocalPosition')}")
