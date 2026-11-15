import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path
import datetime

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
if p.exists():
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
    print(f"blitzwing_gs.assetbundle mtime: {mtime}, size: {p.stat().st_size} bytes")
else:
    print("Does not exist")

p2 = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\atlased_textures\cha_blitzwing_main_RAOE.png")
if p2.exists():
    mtime2 = datetime.datetime.fromtimestamp(p2.stat().st_mtime)
    print(f"cha_blitzwing_main_RAOE.png mtime: {mtime2}")
