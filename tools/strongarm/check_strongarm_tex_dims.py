import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
for f in ["cha_strongarm_main_a.png", "cha_strongarm_main_NM_unity.png", "cha_strongarm_main_tform_misc_RAOE.png",
          "cha_strongarm_vh_a.png", "cha_strongarm_vh_NM_unity.png", "cha_strongarm_vh_tform_misc_RAOE.png"]:
    p = tex_dir / f
    if p.exists():
        im = Image.open(p)
        print(f"{f}: size={im.size}, mode={im.mode}")
    else:
        print(f"MISSING: {p}")
