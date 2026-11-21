import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from PIL import Image

p = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Lights.png"
if os.path.exists(p):
    im = Image.open(p)
    print(f"Body_Lights.png: size={im.size}, mode={im.mode}")
else:
    print("Body_Lights.png does not exist")
