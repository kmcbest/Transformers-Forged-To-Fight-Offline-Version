import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
base_apk = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"

with zipfile.ZipFile(base_apk, "r") as z:
    names = [n for n in z.namelist() if "megatronus" in n.lower() or "necrotronus" in n.lower()]
    print("In base APK:", names)
