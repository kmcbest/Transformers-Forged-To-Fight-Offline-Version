import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

bp = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(bp))

print("Dependencies of prowl bundle:")
for i, dep in enumerate(env.file.deps):
    print(f"  Dep {i}: path={dep.path}, guid={dep.guid}, type={dep.type}")

for i, dep in enumerate(getattr(env.file, 'm_ExternalFiles', [])):
    print(f"  ExtFile {i}: {dep.path}")
