import zipfile
import json

with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    for name in z.namelist():
        if "packs.txt" in name:
            print(f"Found {name}")
            data = z.read(name)
            pdict = json.loads(data.decode('utf-8'))
            print("Packs in blender APK:")
            for k in pdict.get("packs", {}):
                print(f"  {k}")

