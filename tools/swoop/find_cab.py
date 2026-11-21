import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# search in extracted_apk or assets_netflix
for root_dir in [Path(r"E:\Agent\TFTF\extracted_apk\assets"), Path(r"E:\Agent\TFTF\assets_netflix")]:
    for p in root_dir.rglob("*.assetbundle"):
        try:
            env = UnityPy.load(str(p))
            for f in env.file.files.values():
                cab = getattr(f, "name", "")
                if "48a8fb7c" in cab.lower():
                    print(f"Found CAB in {p.name}: {cab}")
                    break
        except:
            pass
