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

# Let's inspect the pocket region:
# Y in [700, 840], X in [785, 875]
sub = arr[700:840, 785:875].copy()
lum = sub.mean(axis=2)

# Silver frame has high brightness lum > 80
# The pocket interior has either red honeycomb (R > G+30) or black cavity (lum < 50)
is_light = (lum < 65) | ((sub[:, :, 0] > sub[:, :, 1] + 25) & (sub[:, :, 0] > sub[:, :, 2] + 25))

# Don't touch silver frame:
is_silver = (lum > 85) & (abs(sub[:, :, 0].astype(int) - sub[:, :, 1].astype(int)) < 25)
is_light = is_light & (~is_silver)

print(f"Sub shape: {sub.shape}, Light pixels to fill: {np.count_nonzero(is_light)}")

sub_filled = sub.copy()
sub_filled[is_light] = [235, 25, 20]

# Overlay on full diff
arr_filled = arr.copy()
arr_filled[700:840, 785:875] = sub_filled

# Save crop around pocket
crop = arr_filled[680:860, 760:900]
Image.fromarray(crop).save(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\pocket_red_perfect_crop.png")
print("Saved pocket_red_perfect_crop.png")
