import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tt = obj.read_typetree()
        print(f"AssetBundle m_Name: {tt.get('m_Name')}")
        print("Container:")
        for k, v in tt.get("m_Container", []):
            asset_ref = v.get("asset", {})
            print(f"  '{k}' -> PID: {asset_ref.get('m_PathID')}")
