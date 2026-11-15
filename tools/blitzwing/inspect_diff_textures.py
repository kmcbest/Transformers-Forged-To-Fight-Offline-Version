import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures")
for name in ["Body_Diffuse.png", "Hands_Diffuse.png", "Legs_Diffuse.png", "Tank_Diffuse.png", "Jet_Diffuse.png", "Treads_Diffuse.png"]:
    im = Image.open(TEX_DIR / name)
    print(f"{name:20s}: size={im.size}, mode={im.mode}")
