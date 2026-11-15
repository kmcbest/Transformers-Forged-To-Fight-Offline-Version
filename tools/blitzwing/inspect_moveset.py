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
    if obj.type.name == "MonoBehaviour":
        try:
            tt = obj.read_typetree()
            if "_moves" in tt:
                print(f"MoveSet PathID {obj.path_id}:")
                for m in tt.get("_moves", []):
                    print(f"  Name: {m.get('_name')}, AnimState: {m.get('_animStateName')}, Asset PID: {m.get('_asset', {}).get('m_PathID')}")
        except:
            pass
