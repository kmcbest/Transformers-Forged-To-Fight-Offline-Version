import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
import re
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
APK_PATH = BASE_DIR / r"build\Transformers-9.2-offline-blender2.apk"

target_cabs = {
    "CAB-7b4e49a3d1aa1dc7f57cab96e5d8d1f7": 1,
    "CAB-47012f9f52e0ee1cac4dfad2d29a972d": 2,
    "CAB-48a8fb7c73226df35ecf6a5823f21dd6": 3,
    "CAB-de7c749530a5ce51ab49ae7f3bcf1777": 4,
    "CAB-ab43fd15c150476227e8346a96b20ca7": 5,
    "CAB-a742a3fff84aa604ba32daca2b1ea500": 6,
}

with zipfile.ZipFile(APK_PATH, "r") as z:
    for name in z.namelist():
        if name.endswith(".assetbundle"):
            data = z.read(name)[:4096]
            for cab in target_cabs:
                if cab.encode("utf-8") in data:
                    print(f"FileID {target_cabs[cab]} ({cab}) is in: {name}")
