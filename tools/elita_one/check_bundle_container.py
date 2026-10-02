import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        data = obj.read()
        print("Container in AssetBundle:")
        for k, v in data.m_Container:
            print(f"  '{k}' -> path_id={v.asset.path_id}")
