import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

print("=== [DragStrip] Stage 1 PBR Atlas Builder (2048 Main + 1024 Weapons) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX = ROOT / "3rd-party-models" / "DragStrip" / "source" / "textures"
OUT_TEX = ROOT / "3rd-party-models" / "DragStrip" / "02_textures"
OUT_TEX.mkdir(parents=True, exist_ok=True)
UNITY_TEX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "DragStrip" / "Textures"
UNITY_TEX.mkdir(parents=True, exist_ok=True)

# 1. Body / Vehicle 2048x2048 PBR
# IMPORTANT: Alliance Tx_Dragstrip_D.png has Alpha=0 across 90.66% of pixels (non-eye surfaces).
# Never resize RGBA directly with LANCZOS or RGB gets premultiplied by 0 (black diffuse!).
orig_d = Image.open(SRC_TEX / "Tx_Dragstrip_D.png")
rgb_arr = np.array(orig_d.convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS))
alpha_orig = np.array(orig_d.convert("RGBA").split()[3].resize((2048, 2048), Image.Resampling.BILINEAR))
n_im = Image.open(SRC_TEX / "Tx_Dragstrip_N.png").convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)
s_im = Image.open(SRC_TEX / "Tx_Dragstrip_S.png").convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)

em_mask = (alpha_orig > 20).astype(np.uint8) * 255
em_pct = (em_mask > 20).mean() * 100.0
print(f"[*] Main Alpha>20 eye glow coverage: {em_pct:.4f}% ({(em_mask>20).sum()} px)")

# Brighten eye pixels cleanly in Diffuse (subtle crimson base so unlit & Unity Standard both look red!)
# and build _Emission.png strictly on eye glow region
em_rgb = np.zeros((2048, 2048, 3), dtype=np.uint8)
eye_idx = alpha_orig > 20
rgb_arr[eye_idx, 0] = np.maximum(rgb_arr[eye_idx, 0], 190)
rgb_arr[eye_idx, 1] = np.minimum(rgb_arr[eye_idx, 1], 25)
rgb_arr[eye_idx, 2] = np.minimum(rgb_arr[eye_idx, 2], 25)
em_rgb[eye_idx] = [255, 25, 25]

# Stamp safe Decepticon Purple & Charcoal backing on verified empty 48x48 UV islands:
#   (0.867188, 0.914062) -> 2048 px (1776, 176) = Purple [165, 42, 232]
#   (0.929688, 0.914062) -> 2048 px (1904, 176) = Charcoal [22, 22, 26]
diff_pil = Image.fromarray(rgb_arr, mode="RGB")
draw_d = ImageDraw.Draw(diff_pil)
draw_d.rectangle([1776 - 48, 176 - 48, 1776 + 48, 176 + 48], fill=(165, 42, 232))
draw_d.rectangle([1904 - 48, 176 - 48, 1904 + 48, 176 + 48], fill=(22, 22, 26))

# Build strict 3-channel RGB RAOE: R=Roughness(255 - S.G), G=AO(S.B), B=Emissive(eye mask)
s_arr = np.array(s_im, dtype=np.float32)
rough = np.clip(255.0 - s_arr[:, :, 1], 130.0, 235.0).astype(np.uint8)
ao = np.clip(s_arr[:, :, 2], 0.0, 255.0).astype(np.uint8)
raoe_arr = np.stack([rough, ao, em_mask], axis=-1)
raoe_pil = Image.fromarray(raoe_arr, mode="RGB")
draw_r = ImageDraw.Draw(raoe_pil)
draw_r.rectangle([1776 - 48, 176 - 48, 1776 + 48, 176 + 48], fill=(175, 255, 0))
draw_r.rectangle([1904 - 48, 176 - 48, 1904 + 48, 176 + 48], fill=(195, 255, 0))

# Build Kabam Normal (NM.B = Metallic Mask from S.R) and Unity OpenGL Normal_unity
n_arr = np.array(n_im, dtype=np.uint8)
n_unity_pil = Image.fromarray(n_arr, mode="RGB")
metal_mask = np.clip(s_arr[:, :, 0] * 0.65, 0.0, 145.0).astype(np.uint8)
n_kabam_arr = np.stack([n_arr[:, :, 0], n_arr[:, :, 1], metal_mask], axis=-1)
n_kabam_pil = Image.fromarray(n_kabam_arr, mode="RGB")
draw_n = ImageDraw.Draw(n_kabam_pil)
draw_n.rectangle([1776 - 48, 176 - 48, 1776 + 48, 176 + 48], fill=(128, 128, 10))
draw_n.rectangle([1904 - 48, 176 - 48, 1904 + 48, 176 + 48], fill=(128, 128, 25))

em_pil = Image.fromarray(em_rgb, mode="RGB")

for base_dir in (OUT_TEX, UNITY_TEX):
    diff_pil.save(base_dir / "cha_dragstrip_main_Diffuse.png")
    raoe_pil.save(base_dir / "cha_dragstrip_main_RAOE.png")
    n_kabam_pil.save(base_dir / "cha_dragstrip_main_Normal.png")
    n_unity_pil.save(base_dir / "cha_dragstrip_main_Normal_unity.png")
    em_pil.save(base_dir / "cha_dragstrip_main_Emission.png")

print(f"[✓] Main 2048 PBR: RoughMean={rough.mean():.1f}, AOMean={ao.mean():.1f}, NM.B Mean={metal_mask.mean():.1f}, Em={em_pct:.3f}%")

# 2. Weapon 1024x1024 PBR
wd_im = Image.open(SRC_TEX / "Tx_Dragstrip_Weapon_D.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
wn_im = Image.open(SRC_TEX / "Tx_Dragstrip_Weapon_N.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
ws_im = Image.open(SRC_TEX / "Tx_Dragstrip_Weapon_S.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)

ws_arr = np.array(ws_im, dtype=np.float32)
w_rough = np.clip(255.0 - ws_arr[:, :, 1], 130.0, 235.0).astype(np.uint8)
w_ao = np.clip(ws_arr[:, :, 2], 0.0, 255.0).astype(np.uint8)
w_em = np.zeros((1024, 1024), dtype=np.uint8)
w_raoe = Image.fromarray(np.stack([w_rough, w_ao, w_em], axis=-1), mode="RGB")

wn_arr = np.array(wn_im, dtype=np.uint8)
w_metal = np.clip(ws_arr[:, :, 0] * 0.70, 0.0, 150.0).astype(np.uint8)
w_kabam_n = Image.fromarray(np.stack([wn_arr[:, :, 0], wn_arr[:, :, 1], w_metal], axis=-1), mode="RGB")

w_em_rgb = Image.fromarray(np.zeros((1024, 1024, 3), dtype=np.uint8), mode="RGB")

for base_dir in (OUT_TEX, UNITY_TEX):
    wd_im.save(base_dir / "cha_dragstrip_wpns_Diffuse.png")
    w_raoe.save(base_dir / "cha_dragstrip_wpns_RAOE.png")
    w_kabam_n.save(base_dir / "cha_dragstrip_wpns_Normal.png")
    wn_im.save(base_dir / "cha_dragstrip_wpns_Normal_unity.png")
    w_em_rgb.save(base_dir / "cha_dragstrip_wpns_Emission.png")
print(f"[✓] Weapon 1024 PBR: RoughMean={w_rough.mean():.1f}, AOMean={w_ao.mean():.1f}, NM.B Mean={w_metal.mean():.1f}")
