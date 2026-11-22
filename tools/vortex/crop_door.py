import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

diff = Image.open('e:/Agent/TFTF-blender/tools/dumped_vortex_tex/tform_misc_A.png')
w, h = diff.size
# U in [0.35..0.50], V in [0.80..0.95]
# in pixel coordinates:
# x in [0.35*w .. 0.50*w], y in [(1.0 - 0.95)*h .. (1.0 - 0.80)*h]
x0, x1 = int(0.35 * w), int(0.50 * w)
y0, y1 = int((1.0 - 0.95) * h), int((1.0 - 0.80) * h)

crop = diff.crop((x0, y0, x1, y1))
crop.save('e:/Agent/TFTF-blender/tools/vortex/crop_door_uv.png')
print("Saved crop_door_uv.png")
