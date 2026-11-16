import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

APK = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
with zipfile.ZipFile(APK, "r") as z:
    for name in z.namelist():
        if "toc.txt" in name and ("brawl" in name or "tarn" in name or "megatron" in name):
            raw = z.read(name)
            has_bom = raw.startswith(b"\xef\xbb\xbf")
            print(f"{name}: len={len(raw)}, BOM={has_bom}, first_bytes={raw[:16]}")
