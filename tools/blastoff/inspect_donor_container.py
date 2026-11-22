import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "AssetBundle":
        tt = o.read_typetree()
        print("m_Name:", tt.get("m_Name"))
        print("m_AssetBundleName:", tt.get("m_AssetBundleName"))
        for k, v in tt.get("m_Container", []):
            print(f"Container entry: '{k}' -> asset={v['asset']}")
