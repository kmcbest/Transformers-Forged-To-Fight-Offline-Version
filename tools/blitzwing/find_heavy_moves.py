import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/moves.assetbundle")
env = UnityPy.load(str(bundle_path))
count = 0
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            data = obj.read()
            name = getattr(data, "name", "")
            if "heavy" in name.lower():
                print(f"{name}")
                count += 1
                if count > 20: break
        except Exception:
            pass
