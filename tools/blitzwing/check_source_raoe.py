import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures")
for name in ["Body_RAOE.png", "Hands_RAOE.png", "Legs_RAOE.png", "Tank_RAOE.png", "Jet_RAOE.png", "Treads_RAOE.png"]:
    p = tex_dir / name
    if p.exists():
        im = Image.open(p)
        print(f"{name:20s}: mode={im.mode}, extrema={im.getextrema()}")
