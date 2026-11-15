import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import subprocess

res = subprocess.check_output(['es.exe', '-n', '5', 'ramjet_gs_deluxe2008.assetbundle'], text=True)
ramjet_path = Path(res.strip().splitlines()[0])
env = UnityPy.load(str(ramjet_path))
obj_map = {o.path_id: o for o in env.objects}

aoc_tt = obj_map[-6340484879223379266].read_typetree()
print("override_Ramjet_GS_Deluxe2008_jet typetree:")
for k, v in aoc_tt.items():
    if k != "m_Clips":
        print(f"  {k}: {v}")
print(f"m_Clips count: {len(aoc_tt['m_Clips'])}")
for idx, c in enumerate(aoc_tt['m_Clips']):
    if c['m_OverrideClip']['m_PathID'] != 0:
        print(f"  Clip {idx}: Orig={c['m_OriginalClip']} -> Sub={c['m_OverrideClip']}")
