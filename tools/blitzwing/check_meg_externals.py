import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

meg_path = Path("E:/Agent/TFTF/assets_ios/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(meg_path))
sf = next(f for f in env.file.files.values() if hasattr(f, 'objects'))
print("Megatron sf.externals:")
for idx, ext in enumerate(getattr(sf, 'externals', [])):
    print(f"  FileID {idx+1}: path='{ext.path}', guid={ext.guid}")
