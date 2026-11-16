import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

APK = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
with zipfile.ZipFile(APK, "r") as z:
    for info in z.infolist():
        if "brawl_gs.assetbundle" in info.filename:
            print(f"{info.filename}: file_size={info.file_size}, compress_size={info.compress_size}")
