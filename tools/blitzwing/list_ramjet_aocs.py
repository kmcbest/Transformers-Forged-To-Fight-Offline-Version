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
        print(f"AOC PID {o.path_id}: Name='{tt.get('m_Name')}'")
