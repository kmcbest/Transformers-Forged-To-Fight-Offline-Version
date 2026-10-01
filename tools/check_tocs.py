import zipfile
import json

with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    names = set(z.namelist())
    
    for toc_name in ["assets/portraits_odr/toc.txt", "assets/questboard_odr/toc.txt", "assets/dialogue_odr/toc.txt"]:
        if toc_name in names:
            data = z.read(toc_name)
            toc = json.loads(data.decode('utf-8'))
            files = toc.get("files", [])
            missing = []
            for f in files:
                # check if file is in apk under assets/assetpack/<pack>/... or assets/<pack>/...
                # e.g. portraits/portrait_foo.png -> assets/assetpack/portraits_odr/portraits/portrait_foo.png
                p1 = f"assets/assetpack/{toc_name.split('/')[1]}/{f}"
                p2 = f"assets/{toc_name.split('/')[1]}/{f}"
                if p1 not in names and p2 not in names:
                    missing.append(f)
            print(f"\n{toc_name}: total {len(files)}, missing {len(missing)}")
            for m in missing[:10]:
                print(f"  MISSING: {m}")
