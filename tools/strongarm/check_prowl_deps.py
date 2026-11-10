import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(bundle_path))

for name, f in env.file.files.items():
    if hasattr(f, 'externals'):
        print(f"Externals in {name}:")
        for i, ext in enumerate(f.externals):
            print(f"  [{i+1}] {ext.name} (guid={ext.guid}, type={ext.type}, path={ext.path})")
