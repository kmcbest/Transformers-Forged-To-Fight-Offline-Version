import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "Material":
        d = obj.read_typetree()
        mname = d.get("m_Name", "")
        print(f"\nMaterial {mname} (PID: {obj.path_id}):")
        envs = d.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        for item in envs:
            if isinstance(item, tuple) and len(item) == 2:
                pname, pdata = item
                tex = pdata.get("m_Texture", {})
                t_pid = tex.get("m_PathID")
                t_obj = obj_map.get(t_pid)
                t_name = t_obj.read_typetree().get("m_Name", "") if t_obj else f"PID:{t_pid}"
                if t_pid != 0:
                    print(f"  {pname}: {t_name}")
