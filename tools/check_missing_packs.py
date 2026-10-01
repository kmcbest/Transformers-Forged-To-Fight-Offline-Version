import zipfile
import json

with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    names = set(z.namelist())
    data = z.read("assets/packs.txt")
    pdict = json.loads(data.decode('utf-8'))
    
    missing_bundles = []
    missing_tocs = []
    
    for pkey in pdict.get("packs", {}):
        # Each pack foo_odr typically has assets/assetpack/foo_odr/foo.assetbundle or assets/foo_odr/toc.txt
        # Let's check what exists for pkey
        has_any = any(pkey in n for n in names)
        if not has_any:
            missing_bundles.append(pkey)
            
    print(f"Total packs in packs.txt: {len(pdict.get('packs', {}))}")
    print(f"Missing packs (NOT A SINGLE FILE in APK): {len(missing_bundles)}")
    for m in missing_bundles:
        print(f"  MISSING: {m}")
