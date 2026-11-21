import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
sf = None
for f in env.file.files.values():
    if hasattr(f, 'externals'):
        sf = f
        break

print("Grimlock Externals:")
for i, e in enumerate(sf.externals):
    print(f"  FileID {i+1}: {e.path}")
