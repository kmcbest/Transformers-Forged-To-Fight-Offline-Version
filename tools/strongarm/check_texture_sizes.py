import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\textures")
for p in sorted(tex_dir.glob("*.png")):
    im = Image.open(p)
    print(f"{p.name}: {im.size}, mode={im.mode}")
