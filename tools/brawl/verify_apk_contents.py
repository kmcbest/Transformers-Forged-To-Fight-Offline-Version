import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
print(f"Checking APK: {apk_path} ({apk_path.stat().st_size / 1024 / 1024:.2f} MB)")

with zipfile.ZipFile(apk_path, "r") as z:
    brawl_entries = [name for name in z.namelist() if "brawl" in name.lower()]
    print(f"\nFound {len(brawl_entries)} Brawl-related files in APK:")
    for name in brawl_entries:
        info = z.getinfo(name)
        print(f"  - {name} ({info.file_size} bytes)")
