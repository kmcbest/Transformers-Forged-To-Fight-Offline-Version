import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r"E:\Agent\TFTF-blender")

ORIG_DIFF_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures" / "T_CH11_00_D.png"
ORIG_GLOW_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures" / "MI_CH11_00_glow.tga.png"
TEX_DIR = ROOT / "tools" / "elita_one" / "processed_textures"

PROCESSED_DIFF_PATH = TEX_DIR / "elita_main_diffuse.png"
PROCESSED_RAOE_PATH = TEX_DIR / "elita_main_raoe.png"

# 1. Base clean Diffuse (1024x1024) from original 2048
orig_diff_2048 = Image.open(ORIG_DIFF_PATH).convert("RGBA")
orig_glow_2048 = Image.open(ORIG_GLOW_PATH).convert("RGBA")

# Extract the exact glow mask from original Galactic Trials glow texture:
# Find true eye glow mask in 2048:
glow_np = np.array(orig_glow_2048)
eye_glow_mask_2048 = np.zeros((2048, 2048), dtype=bool)
# True eye box: Y in [1075, 1105], X in [160, 215]
eye_glow_mask_2048[1075:1105, 160:215] = glow_np[1075:1105, 160:215, 3] > 10

# Resize clean diffuse to 1024
diff_1024 = orig_diff_2048.resize((1024, 1024), Image.LANCZOS)
diff_np = np.array(diff_1024)

# Load current RAOE
raoe_1024 = Image.open(PROCESSED_RAOE_PATH).convert("RGB")
raoe_np = np.array(raoe_1024)

# 2. Completely clean cheeks and face in RAOE:
# Set B = 0 for the entire cheek / lower face area!
raoe_np[:250, :400, 2] = 0

# BUT preserve the yellow visor at the top of the forehead if present:
# Visor in 2048 is Y in [0, 50], X in [680, 1150] -> in 1024: Y in [0, 30], X in [340, 580]
visor_mask_2048 = (glow_np[:100, 680:1160, 0] > 180) & (glow_np[:100, 680:1160, 1] > 150)
if np.any(visor_mask_2048):
    visor_pil = Image.fromarray(visor_mask_2048.astype(np.uint8) * 255).resize((240, 50), Image.BILINEAR)
    visor_1024 = np.array(visor_pil) > 100
    raoe_np[:50, 340:580, 2][visor_1024] = 255

# 3. Downscale true eye glow mask to 1024
eye_mask_pil = Image.fromarray(eye_glow_mask_2048.astype(np.uint8) * 255).resize((1024, 1024), Image.BILINEAR)
eye_mask_1024 = np.array(eye_mask_pil) > 80

# Dilate slightly (1 pixel) to ensure full coverage of the eye geometry
from scipy.ndimage import binary_dilation
eye_mask_1024_dilated = binary_dilation(eye_mask_1024, iterations=1)

# Apply 100% emissive to RAOE.B for the true eyes
raoe_np[eye_mask_1024_dilated, 2] = 255

# Apply vibrant luminous cyan to diffuse for the true eyes
# Inner core: bright white-cyan [180, 245, 255]
# Outer rim: deep electric cyan [80, 210, 240]
diff_np[eye_mask_1024_dilated, :3] = [90, 215, 245]
diff_np[eye_mask_1024, :3] = [170, 245, 255]

# 4. Save updated textures
out_diff = Image.fromarray(diff_np)
out_raoe = Image.fromarray(raoe_np)

out_diff.save(PROCESSED_DIFF_PATH)
out_raoe.save(PROCESSED_RAOE_PATH)

print(f"[?] Successfully cleaned cheeks and applied true eye glow to {PROCESSED_DIFF_PATH}")
print(f"[?] Successfully updated RAOE at true eye coordinates to {PROCESSED_RAOE_PATH}")

# Save visual verification crops
# Cheek area crop:
cheek_crop = out_diff.crop((0, 0, 350, 220))
cheek_crop.save(ROOT / "tools" / "elita_one" / "verify_cheek_clean.png")

# Eye area crop:
eye_crop_diff = out_diff.crop((70, 530, 130, 560))
eye_crop_diff.save(ROOT / "tools" / "elita_one" / "verify_eye_diff.png")

eye_crop_raoe = out_raoe.crop((70, 530, 130, 560))
eye_crop_raoe.save(ROOT / "tools" / "elita_one" / "verify_eye_raoe.png")

print("[?] Saved verification crops.")
