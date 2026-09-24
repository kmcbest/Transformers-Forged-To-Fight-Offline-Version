# -*- coding: utf-8 -*-
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

apk_path = "build/Transformers-9.2-offline-blender.apk"
with zipfile.ZipFile(apk_path, "r") as z:
    for name in z.namelist():
        if "ironhide_cin_rotf" in name:
            info = z.getinfo(name)
            print(f"APK entry: {name}, size: {info.file_size} bytes")
