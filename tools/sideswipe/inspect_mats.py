import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle")
env = UnityPy.load(str(p))

obj_map = {o.path_id: o for o in env.objects}

mat_pids = [6327179545371057975, -6718098035160789545, 5681344350055115988, 5508013112655075757]

for mpid in mat_pids:
    o = obj_map[mpid]
    tt = o.read_typetree()
    print(f"\nMaterial {mpid} ({tt.get('m_Name')}):")
    for prop, val in tt.get("m_SavedProperties", {}).get("m_TexEnvs", []):
        t_pid = val.get("m_Texture", {}).get("m_PathID")
        t_obj = obj_map.get(t_pid)
        t_name = t_obj.read_typetree().get("m_Name") if t_obj else ""
        print(f"  {prop:20s}: PID={t_pid} ({t_name})")
