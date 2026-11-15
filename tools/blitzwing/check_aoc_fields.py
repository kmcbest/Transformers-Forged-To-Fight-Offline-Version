import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path("E:/Agent/TFTF/assets_ios/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

aoc = obj_map[-3258403100930663047].read_typetree()
print("AOC fields:", list(aoc.keys()))
for k, v in aoc.items():
    if k != "m_Overrides":
        print(f"  {k}: {v}")
