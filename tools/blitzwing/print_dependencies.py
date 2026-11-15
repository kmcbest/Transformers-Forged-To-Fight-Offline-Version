import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tt = obj.read_typetree()
        print("PreloadTable:", tt.get("m_PreloadTable", [])[:10])
        print("Dependencies:", tt.get("m_Dependencies", []))

for k, f in env.files.items():
    print("File:", k)
    if hasattr(f, "header"):
        pass
    if hasattr(f, "externals"):
        for ext in f.externals:
            print("  External:", ext.name, ext.path)
