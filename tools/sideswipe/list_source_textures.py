import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

src_tex = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures")
for f in sorted(src_tex.iterdir()):
    if f.suffix.lower() == ".png":
        im = Image.open(f)
        print(f"{f.name}: size={im.size}, mode={im.mode}")
