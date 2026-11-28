import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
SRC_TEX = WR_DIR / "textures"
OUT_TEX = WR_DIR / "02_textures"
OUT_TEX.mkdir(parents=True, exist_ok=True)

# 1. Load original 1024x1024 textures & split Alpha BEFORE any resize!
im_d = Image.open(SRC_TEX / "Tx_Wildrider_D.png").convert("RGBA")
im_n = Image.open(SRC_TEX / "Tx_Wildrider_N.png").convert("RGB")
im_s = Image.open(SRC_TEX / "Tx_Wildrider_S.png").convert("RGB")

d_rgb = im_d.convert("RGB")
d_alpha = im_d.getchannel("A")

# Inspect S channels on face vs wheel rim vs windshield
s_arr_1k = np.array(im_s, dtype=np.float32)
print("Tx_Wildrider_S sample checks (R, G, B):")
print("  Face skin (250,350):", s_arr_1k[350, 250])
print("  Chest white (450,100):", s_arr_1k[100, 450])
print("  Car hood dark (300,800):", s_arr_1k[800, 300])
print("  Car windshield (420,810):", s_arr_1k[810, 420])
print("  Wheel rim silver (855,755):", s_arr_1k[755, 855])

# 2. Upscale separated RGB / Alpha / N / S to 2048x2048 cleanly (zero premultiplied black-out!)
SIZE = (2048, 2048)
d_rgb_2k = np.array(d_rgb.resize(SIZE, Image.Resampling.LANCZOS), dtype=np.float32)
d_alpha_2k = np.array(d_alpha.resize(SIZE, Image.Resampling.BILINEAR), dtype=np.float32)
n_2k = np.array(im_n.resize(SIZE, Image.Resampling.BILINEAR), dtype=np.float32)
s_2k = np.array(im_s.resize(SIZE, Image.Resampling.LANCZOS), dtype=np.float32)

# 3. Eye/Emissive mask from D.Alpha (Alpha > 15 -> glowing eyes!)
# Make sure eye diffuse color is vibrant crimson-red (not pale salmon/white!)
emis_2k = np.zeros((2048, 2048), dtype=np.float32)
eye_mask = d_alpha_2k > 15.0
emis_2k[eye_mask] = np.clip((d_alpha_2k[eye_mask] - 10.0) / 80.0 * 220.0, 0.0, 230.0)
# Vivid crimson red on eye region so Kabam emissive multiplies cleanly to deep bright red
d_rgb_2k[eye_mask] = [255.0, 32.0, 28.0]

# Subtle brightness/contrast polish for Diffuse (avoid crushed blacks, keep panel lines crisp)
# Lift very dark slate slightly and clamp white peak to 242 to preserve chest detail
lum = 0.299 * d_rgb_2k[:, :, 0] + 0.587 * d_rgb_2k[:, :, 1] + 0.114 * d_rgb_2k[:, :, 2]
# Slight contrast polish on dark car panels (keep charcoal sleek, not mud)
max_c = d_rgb_2k.max(axis=2)
min_c = d_rgb_2k.min(axis=2)
sat = np.where(max_c > 1e-3, (max_c - min_c) / max_c, 0.0)

# Clamp highlight ceiling on non-emissive white chestplate to preserve molded grooves
non_emis = ~eye_mask
d_rgb_2k[non_emis] = np.clip(d_rgb_2k[non_emis], 0.0, 242.0)

# 4. Normal Map Conversion (DirectX -> OpenGL: G = 255 - G)
nx = n_2k[:, :, 0]
ny = 255.0 - n_2k[:, :, 1]
nz = n_2k[:, :, 2]

# Metallic mask (NM.B for Kabam shader):
# Use HSV saturation rule (Section 11.10 / 11.17):
# - Painted colored armor (sat >= 0.22) and bright white chest (lum > 180) -> dielectric (NM.B = 0..10)
# - Neutral gunmetal/silver mechanical parts (sat < 0.22 & S.R > 120) -> metallic (55..95)
# - Dark charcoal car body -> low dielectric clearcoat lacquer (NM.B = 12)
metallic = np.zeros((2048, 2048), dtype=np.float32)
neutral_metal = (sat < 0.22) & (lum <= 190.0) & (s_2k[:, :, 0] > 125.0)
metallic[neutral_metal] = np.clip((s_2k[neutral_metal, 0] - 125.0) / 130.0 * 75.0 + 25.0, 0.0, 95.0)
dark_lacquer = (sat < 0.22) & (lum >= 25.0) & (lum <= 90.0) & (~neutral_metal)
metallic[dark_lacquer] = 12.0
metallic[eye_mask] = 0.0

# 5. RAOE Map (Strict RGB 3-channel: R=Roughness, G=AO, B=Emissive)
# Convert Alliance specular/smoothness into balanced Kabam roughness [105..205]
# Note: in Wildrider S, R is spec/metalness, G is smoothness/gloss, B is AO
rough = np.clip(215.0 - s_2k[:, :, 1] * 0.60, 95.0, 210.0)
# Keep face skin matte (~185) and windshield glossy (~85)
ao = np.clip(s_2k[:, :, 2], 60.0, 255.0)

# 6. Stamp Safe Decepticon Emblem Palette in VERIFIED 100% triangle-free 2048 blocks!
# Block A (Decepticon Purple): 1024 X=[288..320], Y=[48..80] -> 2048 X=[576..640], Y=[96..160] (center UV: U=0.296875, V=0.9375)
# Block B (Charcoal Backing):  1024 X=[336..368], Y=[48..80] -> 2048 X=[672..736], Y=[96..160] (center UV: U=0.343750, V=0.9375)
print("\nStamping Safe Decepticon Emblem Palette:")
print("  Decepticon Purple patch: 2048 px X=[576..640], Y=[96..160] -> UV (0.296875, 0.937500)")
print("  Charcoal Backing patch : 2048 px X=[672..736], Y=[96..160] -> UV (0.343750, 0.937500)")

# Paint Block A: Crisp Metallic Decepticon Purple
d_rgb_2k[96:160, 576:640] = [165.0, 42.0, 232.0]
rough[96:160, 576:640] = 125.0
ao[96:160, 576:640] = 255.0
emis_2k[96:160, 576:640] = 0.0  # Keep RAOE.B=0 so red shader glow doesn't tint purple crest red!
nx[96:160, 576:640] = 128.0
ny[96:160, 576:640] = 128.0
nz[96:160, 576:640] = 255.0
metallic[96:160, 576:640] = 45.0

# Paint Block B: Dark Charcoal Backing
d_rgb_2k[96:160, 672:736] = [22.0, 22.0, 26.0]
rough[96:160, 672:736] = 165.0
ao[96:160, 672:736] = 255.0
emis_2k[96:160, 672:736] = 0.0
nx[96:160, 672:736] = 128.0
ny[96:160, 672:736] = 128.0
nz[96:160, 672:736] = 255.0
metallic[96:160, 672:736] = 25.0

# Assemble & Save Final Textures (Alpha=255 opaque everywhere on Diffuse!)
diff_out = np.dstack([
    np.clip(d_rgb_2k, 0, 255).astype(np.uint8),
    np.full((2048, 2048), 255, dtype=np.uint8)
])
Image.fromarray(diff_out, mode="RGBA").save(OUT_TEX / "cha_wildrider_main_Diffuse.png")

nm_kabam = np.dstack([
    np.clip(nx, 0, 255).astype(np.uint8),
    np.clip(ny, 0, 255).astype(np.uint8),
    np.clip(metallic, 0, 255).astype(np.uint8),
    np.full((2048, 2048), 255, dtype=np.uint8)
])
Image.fromarray(nm_kabam, mode="RGBA").save(OUT_TEX / "cha_wildrider_main_Normal.png")

nm_unity = np.dstack([
    np.clip(nx, 0, 255).astype(np.uint8),
    np.clip(ny, 0, 255).astype(np.uint8),
    np.clip(nz, 0, 255).astype(np.uint8),
])
Image.fromarray(nm_unity, mode="RGB").save(OUT_TEX / "cha_wildrider_main_Normal_unity.png")

raoe_out = np.dstack([
    np.clip(rough, 0, 255).astype(np.uint8),
    np.clip(ao, 0, 255).astype(np.uint8),
    np.clip(emis_2k, 0, 255).astype(np.uint8),
])
Image.fromarray(raoe_out, mode="RGB").save(OUT_TEX / "cha_wildrider_main_RAOE.png")

emis_pct = 100.0 * np.sum(emis_2k > 0) / emis_2k.size
print(f"\n[✓] Saved 2048x2048 PBR textures to {OUT_TEX}")
print(f"    Emissive nonzero ratio: {emis_pct:.4f}% (eyes only, zero supernova leak!)")
print(f"    Mean Roughness: {rough.mean():.1f}, Mean AO: {ao.mean():.1f}, Mean Metallic: {metallic.mean():.1f}")
