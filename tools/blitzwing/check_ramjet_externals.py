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
sf = next(f for f in env.file.files.values() if hasattr(f, 'objects'))
print("sf.externals:")
for idx, ext in enumerate(getattr(sf, 'externals', [])):
    print(f"  FileID {idx+1}: path='{ext.path}', guid={ext.guid}")
