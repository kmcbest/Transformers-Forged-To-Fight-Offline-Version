import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

base_dir = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack")

found = []
for p in base_dir.rglob("*.assetbundle"):
    if "megatronus" in p.name.lower():
        found.append(p)

print(f"Found {len(found)} megatronus bundles:")
for p in found:
    print(" ", p)
