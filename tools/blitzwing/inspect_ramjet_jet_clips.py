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

aoc = obj_map[-6340484879223379266].read_typetree()
print("override_Ramjet_GS_Deluxe2008_jet clips:")
for ov in aoc.get("m_Clips", []):
    orig = ov.get("m_OriginalClip")
    sub = ov.get("m_OverrideClip")
    if sub and sub.get("m_PathID") != 0:
        print(f"  Orig={orig.get('m_PathID')} -> Sub={sub.get('m_PathID')}")
