from PIL import Image
import numpy as np
from scipy.ndimage import distance_transform_edt

orig_2048 = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\T_CH11_00_D.png")
orig_arr = np.array(orig_2048)

# The oval is in [920:1035, 245:295]
sub = orig_arr[920:1035, 245:295]
# Socket teal color: R < 100, B > 70
mask_sub = (sub[:, :, 0] < 100) & (sub[:, :, 2] > 70)

# Full 2048 mask
full_mask_2048 = np.zeros((2048, 2048), dtype=bool)
full_mask_2048[920:1035, 245:295] = mask_sub

# Resize mask to 1024
mask_pil = Image.fromarray(full_mask_2048.astype(np.uint8) * 255).resize((1024, 1024), Image.BILINEAR)
oval_mask_1024 = np.array(mask_pil) > 80

print(f"Full oval mask in 1024 has {oval_mask_1024.sum()} pixels.")
ys, xs = np.where(oval_mask_1024)
print(f"1024 bounds: Y=[{ys.min()}, {ys.max()}], X=[{xs.min()}, {xs.max()}]")

# Load current diffuse and RAOE
diff_path = r"E:\Agent\TFTF-blender\tools\elita_one\processed_textures\elita_main_diffuse.png"
raoe_path = r"E:\Agent\TFTF-blender\tools\elita_one\processed_textures\elita_main_raoe.png"

diff_img = Image.open(diff_path).convert("RGBA")
raoe_img = Image.open(raoe_path).convert("RGB")

diff_np = np.array(diff_img)
raoe_np = np.array(raoe_img)

# Set RAOE.B = 255 for the oval!
raoe_np[oval_mask_1024, 2] = 255

# Set Diffuse to bright cyan for the oval!
dist = distance_transform_edt(oval_mask_1024)
max_d = dist.max()

for y, x in zip(ys, xs):
    factor = dist[y, x] / max_d
    r = int(90 * (1.0 - factor) + 180 * factor)
    g = int(210 * (1.0 - factor) + 245 * factor)
    b = 255
    diff_np[y, x, :3] = [r, g, b]

# Save updated textures
Image.fromarray(diff_np).save(diff_path)
Image.fromarray(raoe_np).save(raoe_path)
print("[?] Updated diffuse and RAOE with full user red box oval!")

# Save visual crop of this area
crop_vis = Image.fromarray(diff_np).crop((110, 455, 160, 525))
crop_vis.save(r"E:\Agent\TFTF-blender\tools\elita_one\red_box_painted_vis_full.png")
