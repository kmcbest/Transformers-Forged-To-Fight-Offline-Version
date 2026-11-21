import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

diff = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png")
raoe = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_RAOE.png")

# UV (0.41, 0.61): in image space:
# X = 0.41 * 2048 = 840
# Y = (1 - 0.61) * 2048 = 800
x = int(0.414 * 2048)
y = int((1.0 - 0.615) * 2048)
print(f"Sampling around X={x}, Y={y}:")

diff_arr = np.array(diff)
raoe_arr = np.array(raoe)

box_diff = diff_arr[y-20:y+20, x-20:x+20]
box_raoe = raoe_arr[y-20:y+20, x-20:x+20]

print("Diff RGB mean:", box_diff[:, :, :3].mean(axis=(0, 1)))
print("Diff RGB sample:", box_diff[20, 20])
print("RAOE sample:", box_raoe[20, 20])

# Crop 200x200 around this spot and save to artifacts
crop = diff.crop((x-100, y-100, x+100, y+100))
crop.save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\uv_041_061_crop.png")
print("Saved uv_041_061_crop.png to artifacts.")
