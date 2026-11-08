import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

candidates = ["grindor", "drift", "cyclonus", "windblade"]
base_paths = [
    r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack",
    r"E:\Agent\TFTF\extracted_apk\assets\assetpack",
]

for base in base_paths:
    if not os.path.exists(base):
        continue
    print(f"Checking in {base}:")
    for item in os.listdir(base):
        for c in candidates:
            if c in item.lower():
                print(f"  Found {c}: {item}")
