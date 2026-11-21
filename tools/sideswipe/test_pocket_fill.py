import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

diff_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png"
diff = Image.open(diff_path)
arr = np.array(diff)
print("arr shape:", arr.shape)

patch = arr[700:850, 780:890].copy()

# The true red pixels: R is high and G, B are low
red_pixels = patch[(patch[:, :, 0] > 100) & (patch[:, :, 1] < 40) & (patch[:, :, 2] < 40)]
print("True red pixels count:", len(red_pixels))
if len(red_pixels) > 0:
    print("Mean red:", red_pixels.mean(axis=0))

# Dark cavity: lum < 45
dark_mask = (patch[:, :, :3].mean(axis=2) < 45)
print("Dark cavity pixels:", np.count_nonzero(dark_mask))

patch_filled = patch.copy()
if patch.shape[2] == 4:
    patch_filled[dark_mask] = [225, 25, 20, 255]
else:
    patch_filled[dark_mask] = [225, 25, 20]

Image.fromarray(patch_filled).save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\pocket_filled_preview.png")
print("Saved pocket_filled_preview.png")
