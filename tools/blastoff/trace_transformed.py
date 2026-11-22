import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blastoff_gs.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

def trace_all(tr_pid, path=""):
    tr = obj_map[tr_pid].read_typetree()
    gname = obj_map[tr.get("m_GameObject", {}).get("m_PathID")].read_typetree().get("m_Name")
    curr_path = f"{path}/{gname}" if path else gname
    if "transform" in gname.lower() or "01" in gname:
        print(f"Found: {curr_path} (PID: {tr_pid})")
    for c in tr.get("m_Children", []):
        trace_all(c.get("m_PathID"), curr_path)

trace_all(3076213683770163573)
