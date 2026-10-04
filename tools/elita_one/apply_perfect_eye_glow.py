import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

with open(r"E:\Agent\TFTF-blender\tools\elita_one\perfect_eye_polys.json", "r") as f:
    eye_polys_data = json.load(f)

print(f"Loaded {len(eye_polys_data)} perfect eye polygons.")

# 1. Create 1024x1024 mask of perfect eye polygons
mask_1024 = Image.new("L", (1024, 1024), 0)
draw = ImageDraw.Draw(mask_1024)

for p in eye_polys_data:
    pts = [(int(uv[0]*1024), int((1.0 - uv[1])*1024)) for uv in p['uvs']]
    draw.polygon(pts, fill=255)

mask_np = np.array(mask_1024)
pts = np.where(mask_np > 0)
print(f"Perfect eyes non-zero pixels in 1024x1024: {len(pts[0])}")

# Dilate by 1 pixel for solid coverage
solid_eye_mask = binary_dilation(mask_np > 0, structure=np.ones((3, 3)))
print(f"Dilated solid eye pixels: {np.sum(solid_eye_mask)}")

# 2. Load textures
diff_path = r"E:\Agent\TFTF-blender\tools\elita_one\processed_textures\elita_main_diffuse.png"
raoe_path = r"E:\Agent\TFTF-blender\tools\elita_one\processed_textures\elita_main_raoe.png"

diff_img = Image.open(diff_path).convert("RGBA")
raoe_img = Image.open(raoe_path).convert("RGB")

diff_np = np.array(diff_img)
raoe_np = np.array(raoe_img)

# 3. Clean old leaky emission areas completely:
# A. Clear the lower sill / upper nose bridge leak (Y: 20..50, X: 60..200)
# (Only keep the newly defined solid_eye_mask in that box!)
raoe_np[:50, :220, 2] = 0

# Also restore original diffuse skin color on the old lower triangle leak
d_orig = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\T_CH11_00_D.png").resize((1024, 1024)).convert("RGBA")
d_orig_np = np.array(d_orig)
diff_np[:50, :220] = d_orig_np[:50, :220]

# B. Clear cheeks (Y: 520..570, X: 60..180)
raoe_np[520:570, 60:180, 2] = 0
# C. Clear shoulder/underarm capsules (Y: 410..520, X: 110..150)
raoe_np[410:520, 110:150, 2] = 0

# 4. Now apply the PERFECT eye mask:
# A. Diffuse: set to brilliant luminous white-cyan [230, 250, 255]
diff_np[solid_eye_mask, 0] = 230
diff_np[solid_eye_mask, 1] = 250
diff_np[solid_eye_mask, 2] = 255

# B. RAOE: Channel B (emissive) = 255
raoe_np[solid_eye_mask, 2] = 255

# 5. Save textures
Image.fromarray(diff_np).save(diff_path)
Image.fromarray(raoe_np).save(raoe_path)

print(f"[✓] Saved {diff_path}")
print(f"[✓] Saved {raoe_path}")
print(f"Emissive pixels count: {np.count_nonzero(raoe_np[:, :, 2])}")
