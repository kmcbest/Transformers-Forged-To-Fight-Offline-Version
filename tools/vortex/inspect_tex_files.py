import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
from pathlib import Path

tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\textures")
for f in tex_dir.glob("*"):
    if f.is_file():
        try:
            im = Image.open(f)
            print(f"{f.name:25s}: size={im.size}, mode={im.mode}")
        except Exception:
            pass
