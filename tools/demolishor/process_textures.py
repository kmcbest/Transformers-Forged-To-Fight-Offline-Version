# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

SRC_DIR = Path(r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\textures")
OUT_DIR = Path(r"d:\Agent\tftf\tools\demolishor\textures_processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== Processing Demolishor Textures ===")

# 1. Albedo / Diffuse
diffuse_path = SRC_DIR / "rb_demolishor_normspec_cust_e_mat_inst.jpeg"
print(f"Loading Diffuse from {diffuse_path.name}...")
diffuse_img = Image.open(diffuse_path).convert("RGBA")
# Resize to 1024x1024 for game performance & compatibility
diffuse_1024 = diffuse_img.resize((1024, 1024), Image.Resampling.LANCZOS)
diffuse_out = OUT_DIR / "cha_demolishor_main_a.png"
diffuse_1024.save(diffuse_out, format="PNG")
print(f"[✓] Saved {diffuse_out.name} (1024x1024)")

# 2. Normal Map
normal_path = SRC_DIR / "rb_demolishor_n.jpeg"
print(f"Loading Normal from {normal_path.name}...")
normal_img = Image.open(normal_path).convert("RGB")
normal_1024 = normal_img.resize((1024, 1024), Image.Resampling.LANCZOS)
# Invert Green channel for DirectX (UE3) -> OpenGL (Unity) normal format
norm_arr = np.array(normal_1024)
norm_arr[:, :, 1] = 255 - norm_arr[:, :, 1]
normal_unity = Image.fromarray(norm_arr)
normal_out = OUT_DIR / "cha_demolishor_main_NM.png"
normal_unity.save(normal_out, format="PNG")
print(f"[✓] Saved {normal_out.name} (1024x1024, Inverted G for Unity)")

# 3. RAOE Map (512x512)
# R: Roughness (~65)
# G: AO (~180)
# B: Emissive (from rb_demolishor_e.jpeg)
emissive_path = SRC_DIR / "rb_demolishor_e.jpeg"
emissive_img = Image.open(emissive_path).convert("L").resize((512, 512), Image.Resampling.BILINEAR)
emissive_arr = np.array(emissive_img)

raoe_arr = np.zeros((512, 512, 3), dtype=np.uint8)
raoe_arr[:, :, 0] = 65  # Roughness
raoe_arr[:, :, 1] = 185 # AO
raoe_arr[:, :, 2] = emissive_arr # Emissive glow

raoe_img = Image.fromarray(raoe_arr)
raoe_out = OUT_DIR / "cha_demolishor_main_tform_misc_RAOE.png"
raoe_img.save(raoe_out, format="PNG")
print(f"[✓] Saved {raoe_out.name} (512x512, R=65, G=185, B=Emissive)")
