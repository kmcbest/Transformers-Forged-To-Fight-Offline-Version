import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name in ("GameObject", "MonoBehaviour", "Prefab"):
        try:
            d = obj.read()
            name = getattr(d, "m_Name", "") or getattr(d, "name", "")
            if "projectile" in name.lower() or "bullet" in name.lower():
                print(f"Found in bundle: {obj.type.name} {name}")
        except:
            pass
