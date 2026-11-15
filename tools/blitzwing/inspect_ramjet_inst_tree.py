import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import subprocess

res = subprocess.check_output(['es.exe', '-n', '5', 'ramjet_gs_deluxe2008.assetbundle'], text=True)
ramjet_path = Path(res.strip().splitlines()[0])
env = UnityPy.load(str(ramjet_path))
obj_map = {o.path_id: o for o in env.objects}

inst_go = obj_map[811501443795564437].read_typetree()
print("Combat transformed GO components:", inst_go.get("m_Component"))
for c in inst_go.get("m_Component", []):
    c_pid = c['component']['m_PathID']
    c_obj = obj_map[c_pid]
    if c_obj.type.name == "Transform":
        tr = c_obj.read_typetree()
        print(f"Transform {c_pid} children count: {len(tr.get('m_Children', []))}")
        for ch in tr.get("m_Children", []):
            ch_tr = obj_map[ch['m_PathID']].read_typetree()
            ch_go = obj_map[ch_tr['m_GameObject']['m_PathID']].read_typetree()
            print(f"  Child {ch['m_PathID']}: '{ch_go['m_Name']}'")
