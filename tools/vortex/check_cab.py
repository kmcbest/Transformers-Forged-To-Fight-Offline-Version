import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
        print(f"CAB: {obj.assets_file.name}")
        break

ab_obj = [o for o in env.objects if o.type.name == "AssetBundle"][0]
print(f"AssetBundle Name: {getattr(ab_obj.read(), 'm_AssetBundleName', 'None')}")
