import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

aoc = obj_map[-3258403100930663047].read_typetree()
print("AOC Name:", aoc.get("m_Name"))
print("Controller:", aoc.get("m_Controller"))
print("Overrides:")
for ov in aoc.get("m_Overrides", []):
    orig = ov.get("m_OriginalClip")
    sub = ov.get("m_OverrideClip")
    print(f"  Orig={orig} -> Sub={sub}")
