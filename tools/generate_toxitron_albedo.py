import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

json_path = r"E:\Agent\TFTF-blender\tools\mesh_poly_uvs.json"
base_nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"
base_opt_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_main_a.png"

with open(json_path, "r") as f:
    polys = json.load(f)

width, height = 1024, 1024

# Create 3D class mask image
mask_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(mask_img)

# Encode classes into color ID:
# (1, 0, 0) = GREEN
# (0, 1, 0) = PURPLE
# (0, 0, 1) = SILVER
# (1, 1, 0) = RED (Windshield)
# (1, 0, 1) = YELLOW (Optics)

class_id_colors = {
    "GREEN": (255, 0, 0, 255),
    "PURPLE": (0, 255, 0, 255),
    "SILVER": (0, 0, 255, 255),
    "RED": (255, 255, 0, 255),
    "YELLOW": (255, 0, 255, 255)
}

for item in polys:
    cls = item["cls"]
    uvs = item["uvs"]
    pts = [(int(round(u * (width - 1))), int(round((1.0 - v) * (height - 1)))) for u, v in uvs]
    if len(pts) >= 3:
        draw.polygon(pts, fill=class_id_colors[cls])

# Dilate mask slightly to prevent UV seam bleeding
mask_arr = np.array(mask_img)

# Load base details (we can blend details from Nemesis Prime)
base_img = Image.open(base_nem_path).convert("RGB")
base_arr = np.array(base_img, dtype=np.float32)

# Compute luminance of original texture for shading preservation
lum = (base_arr[:, :, 0] * 0.299 + base_arr[:, :, 1] * 0.587 + base_arr[:, :, 2] * 0.114) / 255.0
# Normalize and enhance contrast slightly
lum_norm = np.clip((lum - 0.05) / 0.85, 0.0, 1.0)
# Tone curve for metallic / paint response
lum_curve = np.power(lum_norm, 0.8)

# Color palettes (Normalized 0..1)
# 1. Acid Green (荧光亮绿)
col_green = np.array([0.72, 0.90, 0.08])
# 2. Poison Purple (剧毒暗紫)
col_purple = np.array([0.33, 0.11, 0.38])
# 3. Gunmetal Silver (冷灰抛光钢)
col_silver = np.array([0.62, 0.65, 0.68])
# 4. Windshield Red / Cracked Amber (暗红蛛网裂纹)
col_red = np.array([0.85, 0.12, 0.14])
# 5. Toxic Optics Yellow (高亮荧光黄)
col_yellow = np.array([1.00, 0.88, 0.05])

out_arr = np.copy(base_arr)

# Masks from 3D classification
is_green = (mask_arr[:, :, 0] == 255) & (mask_arr[:, :, 1] == 0) & (mask_arr[:, :, 2] == 0)
is_purple = (mask_arr[:, :, 0] == 0) & (mask_arr[:, :, 1] == 255) & (mask_arr[:, :, 2] == 0)
is_silver = (mask_arr[:, :, 0] == 0) & (mask_arr[:, :, 1] == 0) & (mask_arr[:, :, 2] == 255)
is_red = (mask_arr[:, :, 0] == 255) & (mask_arr[:, :, 1] == 255) & (mask_arr[:, :, 2] == 0)
is_yellow = (mask_arr[:, :, 0] == 255) & (mask_arr[:, :, 1] == 0) & (mask_arr[:, :, 2] == 255)

# Render Green
for c in range(3):
    # Base paint with ambient occlusion & metallic specular highlights
    out_arr[is_green, c] = np.clip((col_green[c] * 255.0) * (0.35 + 0.65 * lum_curve[is_green]), 0, 255)

# Render Purple
for c in range(3):
    out_arr[is_purple, c] = np.clip((col_purple[c] * 255.0) * (0.30 + 0.70 * lum_curve[is_purple]), 0, 255)

# Render Silver
for c in range(3):
    out_arr[is_silver, c] = np.clip((col_silver[c] * 255.0) * (0.25 + 0.75 * lum_curve[is_silver]), 0, 255)

# Render Windshield Red
for c in range(3):
    out_arr[is_red, c] = np.clip((col_red[c] * 255.0) * (0.20 + 0.80 * lum_curve[is_red]), 0, 255)

# Render Optics Yellow
for c in range(3):
    out_arr[is_yellow, c] = np.clip((col_yellow[c] * 255.0) * (0.50 + 0.50 * lum_curve[is_yellow]), 0, 255)

# Add Spiderweb shatter pattern to Windshield area
# We can create a subtle crack overlay on is_red
y_coords, x_coords = np.where(is_red)
if len(y_coords) > 0:
    # Generate procedural shatter noise on windshield
    crack_noise = (np.sin(x_coords * 0.15) * np.cos(y_coords * 0.15) > 0.65) | \
                  (np.sin(x_coords * 0.08 + y_coords * 0.08) > 0.85)
    for c in range(3):
        # bright orange/amber cracks
        crack_color = [255, 160, 40][c]
        out_arr[y_coords[crack_noise], c] = crack_color

# Save result
result_img = Image.fromarray(out_arr.astype(np.uint8))
save_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_toxitron_main_a.png"
result_img.save(save_path)
print(f"Saved generated Toxitron Albedo to {save_path}")
