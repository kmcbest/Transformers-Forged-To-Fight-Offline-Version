import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

regions_json = r"E:\Agent\TFTF-blender\tools\mesh_poly_regions.json"
opt_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_main_a.png"
nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"

with open(regions_json, "r") as f:
    poly_regions = json.load(f)

width, height = 1024, 1024

# Create individual binary region masks from 3D polygons
region_images = {
    "FEET": Image.new("L", (width, height), 0),
    "SHINS": Image.new("L", (width, height), 0),
    "THIGHS": Image.new("L", (width, height), 0),
    "PELVIS": Image.new("L", (width, height), 0),
    "MIDRIFF": Image.new("L", (width, height), 0),
    "CHEST_CAB": Image.new("L", (width, height), 0),
    "WINDSHIELD": Image.new("L", (width, height), 0),
    "HEAD": Image.new("L", (width, height), 0),
    "EYES": Image.new("L", (width, height), 0),
    "HANDS": Image.new("L", (width, height), 0),
    "FOREARMS": Image.new("L", (width, height), 0),
    "SHOULDERS": Image.new("L", (width, height), 0),
    "SMOKESTACKS": Image.new("L", (width, height), 0)
}

draw_map = {k: ImageDraw.Draw(v) for k, v in region_images.items()}

for item in poly_regions:
    reg = item["region"]
    uvs = item["uvs"]
    pts = [(int(round(u * (width - 1))), int(round((1.0 - v) * (height - 1)))) for u, v in uvs]
    if len(pts) >= 3 and reg in draw_map:
        draw_map[reg].polygon(pts, fill=255)

# Convert region images to boolean numpy arrays
masks = {k: (np.array(v) > 128) for k, v in region_images.items()}

# Load official Optimus and Nemesis textures
opt_arr = np.array(Image.open(opt_path).convert("RGB"), dtype=np.float32)
nem_arr = np.array(Image.open(nem_path).convert("RGB"), dtype=np.float32)

# Use Nemesis Prime as the base material detail source (panel lines, AO, screws, specular highlights)
lum_nem = (0.299 * nem_arr[:, :, 0] + 0.587 * nem_arr[:, :, 1] + 0.114 * nem_arr[:, :, 2]) / 255.0
lum_curve = np.power(np.clip(lum_nem * 1.35, 0.05, 1.0), 0.85)

# High-precision 2D masks from Optimus Prime (to refine sub-pixel mechanical boundaries)
is_opt_red = (opt_arr[:, :, 0] > opt_arr[:, :, 1] + 25) & (opt_arr[:, :, 0] > opt_arr[:, :, 2] + 25)
is_opt_blue = (opt_arr[:, :, 2] > opt_arr[:, :, 0] + 15) & (opt_arr[:, :, 2] > opt_arr[:, :, 1] - 5)
is_opt_silver = (~is_opt_red) & (~is_opt_blue)

# Initialize output with Nemesis base
out_arr = np.copy(nem_arr)

# Color palettes (Normalized 0..1 RGB)
COL_ACID_GREEN = np.array([0.71, 0.88, 0.09])    # #B5E017 Toxic Lime Green
COL_DARK_PURPLE = np.array([0.31, 0.10, 0.35])   # #4F1A5A Deep Poison Purple
COL_GUNMETAL = np.array([0.58, 0.62, 0.65])      # #949EA6 Metallic Gunmetal Silver
COL_WINDSHIELD_RED = np.array([0.82, 0.12, 0.14])# #D11F24 Dark Crimson
COL_OPTICS_YELLOW = np.array([1.00, 0.85, 0.04]) # #FFD90A Toxic Amber Eyes

def apply_color(target_mask, col_norm, base_shade=0.35, highlight_shade=0.65):
    for c in range(3):
        out_arr[target_mask, c] = np.clip(
            (col_norm[c] * 255.0) * (base_shade + highlight_shade * lum_curve[target_mask]),
            0, 255
        )

# 1. Acid Green regions:
mask_green = masks["CHEST_CAB"] | masks["FOREARMS"] | masks["SHOULDERS"] | (masks["SHINS"] & is_opt_blue)
mask_green = mask_green | (is_opt_red & ~masks["WINDSHIELD"] & ~masks["HEAD"])
mask_green = mask_green & ~masks["WINDSHIELD"] & ~masks["HEAD"] & ~masks["PELVIS"] & ~masks["FEET"] & ~masks["HANDS"] & ~masks["MIDRIFF"] & ~masks["THIGHS"]

apply_color(mask_green, COL_ACID_GREEN, 0.38, 0.62)

# 2. Deep Poison Purple regions:
mask_purple = (masks["HEAD"] & ~masks["EYES"]) | masks["FEET"] | masks["PELVIS"] | masks["HANDS"] | masks["SMOKESTACKS"]
apply_color(mask_purple, COL_DARK_PURPLE, 0.28, 0.72)

# 3. Metallic Gunmetal / Silver regions:
mask_silver = masks["THIGHS"] | masks["MIDRIFF"] | (is_opt_silver & ~mask_purple & ~mask_green & ~masks["WINDSHIELD"])
apply_color(mask_silver, COL_GUNMETAL, 0.25, 0.75)

# 4. Windshield Red
mask_windshield = masks["WINDSHIELD"]
apply_color(mask_windshield, COL_WINDSHIELD_RED, 0.20, 0.80)

# Add spiderweb crack effect to windshield
y_win, x_win = np.where(mask_windshield)
if len(y_win) > 0:
    cracks = ((np.sin(x_win * 0.18) * np.cos(y_win * 0.18) > 0.60) |
              (np.sin(x_win * 0.10 + y_win * 0.10) > 0.82))
    for c in range(3):
        out_arr[y_win[cracks], c] = [255, 175, 45][c]

# 5. Glowing Optics Yellow
mask_optics = masks["EYES"]
apply_color(mask_optics, COL_OPTICS_YELLOW, 0.60, 0.40)

# Save the polished Albedo
result_img = Image.fromarray(out_arr.astype(np.uint8))
save_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_toxitron_main_a.png"
result_img.save(save_path)
print(f"[OK] Polished Toxitron Albedo saved to {save_path}")
