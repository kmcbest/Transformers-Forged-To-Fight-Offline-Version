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

cannon_aoc = obj_map[-4914847298671604126].read_typetree()
print("Cannon AOC name:", cannon_aoc.get("m_Name"))
print("Cannon AOC controller:", cannon_aoc.get("m_Controller"))
print("Cannon AOC m_Clips count:", len(cannon_aoc.get("m_Clips", [])))
for idx, c in enumerate(cannon_aoc.get("m_Clips", [])):
    if c['m_OverrideClip']['m_PathID'] != 0:
        print(f"  [{idx}] Orig={c['m_OriginalClip']} -> Sub={c['m_OverrideClip']}")
