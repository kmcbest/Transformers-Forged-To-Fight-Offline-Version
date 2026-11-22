import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from PIL import Image
import io

with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    data = z.read("textures/DecepticonLogo.png")
    img = Image.open(io.BytesIO(data))
    print("DecepticonLogo size:", img.size, "mode:", img.mode)
    img.save(r"e:\Agent\TFTF-blender\tools\vortex\DecepticonLogo.png")
    print("Saved tools/vortex/DecepticonLogo.png")
