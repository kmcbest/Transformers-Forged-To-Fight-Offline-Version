import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"
env = UnityPy.load(str(SS_BUNDLE))

print("=== Inspecting MoveSet in Sideswipe ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_moves" in tt:
            print(f"MoveSet PID={o.path_id}: name={tt.get('m_Name')}")
            for i, m in enumerate(tt.get("_moves", [])):
                print(f"  Move {i:02d}: name='{m.get('_name')}', asset={m.get('_asset')}")
