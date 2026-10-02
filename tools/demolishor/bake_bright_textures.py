import shutil
import sys
from PIL import Image, ImageEnhance
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = Path("tools/demolishor/textures_processed")
diffuse_path = OUT_DIR / "cha_demolishor_main_a.png"
backup_path = OUT_DIR / "cha_demolishor_main_a_orig.png"

if not backup_path.exists():
    shutil.copy2(diffuse_path, backup_path)
    print(f"Backed up original to {backup_path.name}")

img = Image.open(backup_path).convert("RGBA")
arr = np.array(img, dtype=np.float32)

rgb = arr[:, :, :3]
alpha = arr[:, :, 3]

# Gamma correction: gamma = 0.70 lifts shadows and midtones significantly
gamma = 0.68
rgb_gamma = 255.0 * ((rgb / 255.0) ** gamma)

# Gain 1.30x
rgb_bright = np.clip(rgb_gamma * 1.32, 0, 255).astype(np.uint8)
bright_img = Image.fromarray(rgb_bright)

# Enhance color saturation (+25%) so the golden-yellow armor and maroon accents pop vibrantly
enh_color = ImageEnhance.Color(bright_img)
vibrant_img = enh_color.enhance(1.28)

# Enhance contrast (+12%) for crisp mechanical detail
enh_contrast = ImageEnhance.Contrast(vibrant_img)
final_rgb = enh_contrast.enhance(1.12)

# Re-combine alpha
final_arr = np.dstack((np.array(final_rgb), alpha.astype(np.uint8)))
final_img = Image.fromarray(final_arr, mode="RGBA")
final_img.save(diffuse_path, format="PNG")

print(f"[✓] Saved Brightened Diffuse: {diffuse_path}")
print(f"    Original Means: R=60.1, G=53.7, B=44.4 (Overall: 52.7)")
print(f"    New Means:      R={final_arr[:,:,0].mean():.1f}, G={final_arr[:,:,1].mean():.1f}, B={final_arr[:,:,2].mean():.1f} (Overall: {final_arr[:,:,:3].mean():.1f})")

# Optimize RAOE Map:
raoe_path = OUT_DIR / "cha_demolishor_main_tform_misc_RAOE.png"
raoe_img = Image.open(raoe_path).convert("RGB")
raoe_arr = np.array(raoe_img)
raoe_arr[:, :, 0] = 140 # Satin roughness, prevents chrome mirror reflections
raoe_arr[:, :, 1] = 215 # Bright AO
raoe_arr[:, :, 2] = np.clip(raoe_arr[:, :, 2] * 1.5, 0, 255) # Decepticon purple glow boost
Image.fromarray(raoe_arr).save(raoe_path, format="PNG")
print(f"[✓] Saved Optimized Bright RAOE: {raoe_path}")

# Also brighten vehicle diffuse for consistency!
vh_path = OUT_DIR / "cha_demolishor_vh_a.png"
vh_backup = OUT_DIR / "cha_demolishor_vh_a_orig.png"
if vh_path.exists():
    if not vh_backup.exists():
        shutil.copy2(vh_path, vh_backup)
    vh_img = Image.open(vh_backup).convert("RGBA")
    vh_arr = np.array(vh_img, dtype=np.float32)
    vh_rgb = 255.0 * ((vh_arr[:, :, :3] / 255.0) ** 0.70)
    vh_rgb = np.clip(vh_rgb * 1.30, 0, 255).astype(np.uint8)
    vh_bright = ImageEnhance.Color(Image.fromarray(vh_rgb)).enhance(1.25)
    vh_final = ImageEnhance.Contrast(vh_bright).enhance(1.10)
    vh_out_arr = np.dstack((np.array(vh_final), vh_arr[:, :, 3].astype(np.uint8)))
    Image.fromarray(vh_out_arr, mode="RGBA").save(vh_path, format="PNG")
    print(f"[✓] Brightened Vehicle Diffuse: {vh_path}")
