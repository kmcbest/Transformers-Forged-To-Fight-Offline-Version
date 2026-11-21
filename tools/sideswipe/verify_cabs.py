import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

APK = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
cabs = {
    "CAB-de7c749530a5ce51ab49ae7f3bcf1777": "FileID 1",
    "CAB-69d4b67d9f5d08a3fd32de8fcf679231": "FileID 2",
    "CAB-7b4e49a3d1aa1dc7f57cab96e5d8d1f7": "FileID 3",
    "CAB-47012f9f52e0ee1cac4dfad2d29a972d": "FileID 4",
    "CAB-48a8fb7c73226df35ecf6a5823f21dd6": "FileID 5",
    "CAB-a742a3fff84aa604ba32daca2b1ea500": "FileID 6",
    "CAB-ab43fd15c150476227e8346a96b20ca7": "FileID 8",
}

with zipfile.ZipFile(APK, "r") as z:
    for name in z.namelist():
        if name.endswith(".assetbundle"):
            head = z.read(name)[:4096]
            for c, fid in list(cabs.items()):
                if c.encode("utf-8") in head:
                    print(f"{fid} ({c}) -> {name}")
