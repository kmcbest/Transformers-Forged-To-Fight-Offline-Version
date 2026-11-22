import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blastoff_gs.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        name = tt.get("m_Name")
        if "01" in name or "veh" in name.lower():
            print(f"GO: {name} (PID: {o.path_id})")
            for c in tt.get("m_Component", []):
                cp = obj_map.get(c.get("component", {}).get("m_PathID"))
                if cp and cp.type.name == "Transform":
                    ctr = cp.read_typetree()
                    f_pid = ctr.get("m_Father", {}).get("m_PathID")
                    f_go = obj_map.get(f_pid)
                    f_name = "None"
                    if f_go and f_go.type.name == "Transform":
                        fg_obj = obj_map.get(f_go.read_typetree().get("m_GameObject", {}).get("m_PathID"))
                        f_name = fg_obj.read_typetree().get("m_Name") if fg_obj else "unknown"
                    print(f"  Father: {f_name} (PID: {f_pid}), scale={ctr.get('m_LocalScale')}")
