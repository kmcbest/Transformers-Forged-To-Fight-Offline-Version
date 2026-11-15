import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\atlased_textures")
for p in tex_dir.glob("*.png"):
    im = Image.open(p)
    print(f"{p.name}: size={im.size}, mode={im.mode}")
