import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path

target_cab = b"CAB-48a8fb7c73226df35ecf6a5823f21dd6"

search_roots = [
    Path(r"E:\Agent\TFTF\extracted_apk\assets"),
    Path(r"E:\Agent\TFTF\assets_ios"),
    Path(r"E:\Agent\TFTF\assets_netflix"),
    Path(r"E:\Agent\TFTF-blender")
]

found = []
for root in search_roots:
    if not root.exists():
        continue
    for p in root.rglob("*.assetbundle"):
        try:
            with open(p, "rb") as f:
                data = f.read(4096) # usually in header or early
                if target_cab in data:
                    found.append(p)
                    print(f"Found in header of: {p}")
                    continue
                # If not in first 4096, scan up to 64KB
                data += f.read(60000)
                if target_cab in data:
                    found.append(p)
                    print(f"Found in first 64KB of: {p}")
        except Exception:
            pass

print(f"Total found: {len(found)}")
