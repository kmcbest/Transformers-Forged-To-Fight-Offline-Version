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
for o in env.objects:
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        if "jet" in tt.get("m_Name", "").lower():
            print(f"Jet AOC PID {o.path_id}: Name='{tt.get('m_Name')}'")
            for ov in tt.get("m_Clips", []):
                orig = ov.get("m_OriginalClip")
                sub = ov.get("m_OverrideClip")
                # find sub name in env if possible
                sub_name = ""
                if sub and sub.get("m_PathID") in {x.path_id for x in env.objects}:
                    sub_name = [x.read_typetree().get("m_Name") for x in env.objects if x.path_id == sub.get("m_PathID")][0]
                print(f"  Orig={orig} -> Sub={sub} ({sub_name})")
