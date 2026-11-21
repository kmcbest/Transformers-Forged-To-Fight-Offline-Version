import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

src_diff = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")
src_emis = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Emission.png")

w, h = src_diff.size
x = int(0.414 * w)
y = int((1.0 - 0.615) * h)

crop_diff = src_diff.crop((x-200, y-200, x+200, y+200))
crop_diff.save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\source_uv_041_061_crop.png")

crop_emis = src_emis.crop((x-200, y-200, x+200, y+200))
crop_emis.save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\source_uv_041_061_emis_crop.png")

print(f"Cropped at 4096 coords ({x}, {y})")
