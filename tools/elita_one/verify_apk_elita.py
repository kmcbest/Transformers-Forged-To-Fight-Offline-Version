import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender.apk")
with zipfile.ZipFile(apk_path, 'r') as z:
    for name in z.namelist():
        if "elita_one_gs.assetbundle" in name:
            info = z.getinfo(name)
            print(f"Found embedded bundle in APK: {name} (size: {info.file_size / (1024*1024):.2f} MB)")
