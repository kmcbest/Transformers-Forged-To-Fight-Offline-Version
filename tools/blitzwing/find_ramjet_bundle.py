import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# Find Ramjet's assetbundle
for p in Path(r"E:\Agent\TFTF-blender").rglob("*ramjet*.assetbundle"):
    print("Found bundle:", p)

for p in Path(r"E:\Agent\TFTF\extracted_apk").rglob("*ramjet*.assetbundle"):
    print("Found in TFTF:", p)
