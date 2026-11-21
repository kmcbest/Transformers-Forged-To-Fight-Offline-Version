import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
base_apk = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
out_dir = ROOT / "extracted_apk"

with zipfile.ZipFile(base_apk, "r") as z:
    for n in z.namelist():
        if "necrotronus_gs_kabam" in n or "megatronus_gs_kabam" in n:
            z.extract(n, out_dir)
            print(f"Extracted: {n}")
