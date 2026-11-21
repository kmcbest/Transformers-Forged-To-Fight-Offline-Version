import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

diff_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png"
diff = Image.open(diff_path)
w, h = diff.size

# U in [0.08, 0.18], V in [0.65, 0.75]
x0 = int(0.08 * w)
x1 = int(0.18 * w)
y0 = int((1.0 - 0.75) * h)
y1 = int((1.0 - 0.65) * h)

crop = diff.crop((x0, y0, x1, y1))
crop.save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\uv_013_070_crop.png")
print("Saved uv_013_070_crop.png")
