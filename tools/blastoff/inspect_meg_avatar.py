import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(p))

for o in env.objects:
    if o.type.name == "Avatar":
        tt = o.read_typetree()
        print("Avatar:", tt.get("m_Name"))
        tos = tt.get("m_TOS")
        if isinstance(tos, dict):
            for k in list(tos.keys())[:5]:
                print(f"  dict TOS {k}: {tos[k]}")
        elif isinstance(tos, list):
            for item in tos[:5]:
                print(f"  list item: {item}")
