import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path
import datetime

p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
print(f"blitzwing_mesh.assetbundle mtime: {datetime.datetime.fromtimestamp(p_bundle.stat().st_mtime)}")

for name in ("cha_blitzwing_gs_00_atlased.asset", "cha_blitzwing_gs_01_atlased.asset", "cha_blitzwing_gs_02_atlased.asset"):
    p = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Models") / name
    if p.exists():
        print(f"  {name} mtime: {datetime.datetime.fromtimestamp(p.stat().st_mtime)}")
    else:
        print(f"  {name} NOT FOUND")
