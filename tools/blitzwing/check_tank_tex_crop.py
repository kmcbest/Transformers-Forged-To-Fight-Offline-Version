import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
from pathlib import Path

tex_path = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\atlased_textures\cha_blitzwing_tform_misc_Diffuse.png")
img = Image.open(tex_path)
print(f"Texture: {tex_path.name}, size={img.size}")

# Top-Left 1024x1024 is Tank (V1)
crop_tank = img.crop((0, 0, 1024, 1024))
crop_tank.save(r"E:\Agent\TFTF-blender\tools\blitzwing\renders\check_tank_tex_crop.png")
print("Saved tank crop to renders/check_tank_tex_crop.png")
