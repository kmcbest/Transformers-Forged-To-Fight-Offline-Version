import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

p = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\renders\09_vehicle_modes_overview.png")
if p.exists():
    im = Image.open(p)
    print(f"09_vehicle_modes_overview.png: {im.size}, mode={im.mode}")
else:
    print("09_vehicle_modes_overview.png does not exist")
