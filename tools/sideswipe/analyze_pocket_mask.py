import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

diff = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png")
arr = np.array(diff)

# In 2048 space:
# U in [0.385, 0.435] -> X in [788, 891]
# V in [0.585, 0.655] -> Y in [(1-0.655)*2048, (1-0.585)*2048] = [706, 850]
crop = arr[700:860, 780:900]
print("Crop shape:", crop.shape)

# Let's see the luminance and colors in this crop:
# Silver metal has high luminance with R ~ G ~ B
# Red honeycomb has R > 50, G < 20, B < 20
# Black cavity has R < 35, G < 35, B < 35
lum = crop[:, :, :3].mean(axis=2)
silver_mask = (lum > 100) & (abs(crop[:, :, 0].astype(int) - crop[:, :, 1].astype(int)) < 30)
black_mask = (lum < 40)
red_mask = (crop[:, :, 0].astype(int) > crop[:, :, 1].astype(int) + 30)

print(f"Pixels in 160x120 box: total={crop.shape[0]*crop.shape[1]}")
print(f"  Silver frame: {np.count_nonzero(silver_mask)}")
print(f"  Black cavity: {np.count_nonzero(black_mask)}")
print(f"  Red honeycomb: {np.count_nonzero(red_mask)}")

# Let's save a colored visualization of the masks
vis = np.zeros((160, 120, 3), dtype=np.uint8)
vis[silver_mask] = [200, 200, 200]
vis[black_mask] = [0, 0, 255] # Blue for black cavity
vis[red_mask] = [255, 0, 0] # Red for red honeycomb

Image.fromarray(vis).save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\pocket_mask_vis.png")
print("Saved pocket_mask_vis.png to artifacts.")
