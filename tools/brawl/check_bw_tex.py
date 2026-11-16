import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

p = Path("tools/blitzwing/atlased_textures")
for f in sorted(p.glob("*.png")):
    img = Image.open(f)
    print(f"{f.name}: size={img.size}, mode={img.mode}")
