import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\textures")

for f in sorted(tex_dir.glob("*")):
    if f.suffix.lower() in [".jpg", ".png", ".jpeg"]:
        with Image.open(f) as img:
            print(f"{f.name:45s} | size: {img.size[0]}x{img.size[1]} | mode: {img.mode}")
