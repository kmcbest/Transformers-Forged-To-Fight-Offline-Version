import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
from pathlib import Path

tex_dir = Path(r"e:\Agent\TFTF-blender\tools\blitzwing\atlased_textures")
for p in sorted(tex_dir.glob("*.png")):
    img = Image.open(p)
    print(f"{p.name}: size={img.size} mode={img.mode}")
