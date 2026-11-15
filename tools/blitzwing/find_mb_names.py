import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/moves.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tt = obj.read_typetree()
            name = tt.get("m_Name", "")
            if "megatron" in name.lower() or "blitzwing" in name.lower():
                print(f"PathID={obj.path_id}: {name}")
        except Exception:
            pass
