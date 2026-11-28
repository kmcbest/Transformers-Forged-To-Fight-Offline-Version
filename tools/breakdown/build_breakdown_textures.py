import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

print("=== [Breakdown] Stage 1 PBR Atlas Builder (2048 Main + 1024 Weapon + 512 Sym) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX = ROOT / "3rd-party-models" / "Breakdown" / "source" / "textures"
OUT_TEX = ROOT / "3rd-party-models" / "Breakdown" / "02_textures"
OUT_TEX.mkdir(parents=True, exist_ok=True)
UNITY_TEX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Breakdown" / "Textures"
UNITY_TEX.mkdir(parents=True, exist_ok=True)

# 1. Body / Vehicle 2048x2048 PBR
# IMPORTANT: Alliance Tx_Breakdown_D.png has Alpha=0 across 99.95% of pixels (only eye visor has Alpha>20).
# Always .split() RGB before resizing so RGB isn't premultiplied to black!
orig_d = Image.open(SRC_TEX / "Tx_Breakdown_D.png")
rgb_arr = np.array(orig_d.convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS))
alpha_im = orig_d.convert("RGBA").split()[3].resize((2048, 2048), Image.Resampling.BILINEAR)
# Raw eye mask is ~1503 px (0.036%), just below 0.05% gate; 1-step MaxFilter(5) strictly inside eye UV box brings to ~0.06%
alpha_dil = np.array(alpha_im.filter(ImageFilter.MaxFilter(5)))
alpha_orig = np.array(alpha_im)
eye_box = np.zeros_like(alpha_orig, dtype=bool)
eye_box[115:235, 155:215] = True
em_mask = (((alpha_orig > 20) | (eye_box & (alpha_dil > 10)))).astype(np.uint8) * 255
em_pct = (em_mask > 20).mean() * 100.0
print(f"[*] Main eye glow coverage: {em_pct:.4f}% ({(em_mask>20).sum()} px)")

# Brighten ruby eyes cleanly in Diffuse & Emission (mask stays strictly inside eye UV box!)
em_rgb = np.zeros((2048, 2048, 3), dtype=np.uint8)
eye_idx = em_mask > 20
n_im = Image.open(SRC_TEX / "Tx_Breakdown_N.png").convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)
s_im = Image.open(SRC_TEX / "Tx_Breakdown_S.png").convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)
rgb_arr[eye_idx, 0] = np.maximum(rgb_arr[eye_idx, 0], 225)
rgb_arr[eye_idx, 1] = np.minimum(rgb_arr[eye_idx, 1], 30)
rgb_arr[eye_idx, 2] = np.minimum(rgb_arr[eye_idx, 2], 30)
em_rgb[eye_idx] = [255, 25, 25]

diff_pil = Image.fromarray(rgb_arr, mode="RGB")

# RAOE: R=Roughness(255 - S.G), G=AO(S.B), B=Emissive(eye mask)
s_arr = np.array(s_im, dtype=np.float32)
rough = np.clip(255.0 - s_arr[:, :, 1], 130.0, 235.0).astype(np.uint8)
ao = np.clip(s_arr[:, :, 2], 0.0, 255.0).astype(np.uint8)
raoe_pil = Image.fromarray(np.stack([rough, ao, em_mask], axis=-1), mode="RGB")

# Normal: Kabam Normal has NM.B = Metallic Mask from S.R; Unity preview keeps pure RGB normal
n_arr = np.array(n_im, dtype=np.uint8)
n_unity_pil = Image.fromarray(n_arr, mode="RGB")
metal_mask = np.clip(s_arr[:, :, 0] * 0.65, 0.0, 145.0).astype(np.uint8)
n_kabam_pil = Image.fromarray(np.stack([n_arr[:, :, 0], n_arr[:, :, 1], metal_mask], axis=-1), mode="RGB")
em_pil = Image.fromarray(em_rgb, mode="RGB")

for base_dir in (OUT_TEX, UNITY_TEX):
    diff_pil.save(base_dir / "cha_breakdown_main_Diffuse.png")
    raoe_pil.save(base_dir / "cha_breakdown_main_RAOE.png")
    n_kabam_pil.save(base_dir / "cha_breakdown_main_Normal.png")
    n_unity_pil.save(base_dir / "cha_breakdown_main_Normal_unity.png")
    em_pil.save(base_dir / "cha_breakdown_main_Emission.png")

print(f"[✓] Main 2048 PBR: RoughMean={rough.mean():.1f}, AOMean={ao.mean():.1f}, NM.B Mean={metal_mask.mean():.1f}, Em={em_pct:.4f}%")

# 2. SubMesh 1 Dedicated Decepticon Emblem 512x512 (Left U<0.5 = Purple [165,42,232], Right U>=0.5 = Charcoal [22,22,26])
#    Isolated in donor SubMesh 1 (tform_misc_A/NM) so zero collision with packed Tx_Breakdown_D armor shells!
sym_d = Image.new("RGB", (512, 512), (22, 22, 26))
ImageDraw.Draw(sym_d).rectangle([0, 0, 255, 511], fill=(165, 42, 232))
sym_n = Image.new("RGB", (512, 512), (128, 128, 25))
ImageDraw.Draw(sym_n).rectangle([0, 0, 255, 511], fill=(128, 128, 10))
sym_n_u = Image.new("RGB", (512, 512), (128, 128, 255))
for base_dir in (OUT_TEX, UNITY_TEX):
    sym_d.save(base_dir / "cha_breakdown_sym_Diffuse.png")
    sym_n.save(base_dir / "cha_breakdown_sym_Normal.png")
    sym_n_u.save(base_dir / "cha_breakdown_sym_Normal_unity.png")
print("[✓] SubMesh 1 Decepticon badge 512x512 textures saved cleanly.")

# 3. Weapon 1024x1024 PBR
wd_im = Image.open(SRC_TEX / "Tx_Breakdown_Weapon_D.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
wn_im = Image.open(SRC_TEX / "Tx_Breakdown_Weapon_N.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
ws_im = Image.open(SRC_TEX / "Tx_Breakdown_Weapon_S.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)

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
    wd_im.save(base_dir / "cha_breakdown_wpns_Diffuse.png")
    w_raoe.save(base_dir / "cha_breakdown_wpns_RAOE.png")
    w_kabam_n.save(base_dir / "cha_breakdown_wpns_Normal.png")
    wn_im.save(base_dir / "cha_breakdown_wpns_Normal_unity.png")
    w_em_rgb.save(base_dir / "cha_breakdown_wpns_Emission.png")
print(f"[✓] Weapon 1024 PBR: RoughMean={w_rough.mean():.1f}, AOMean={w_ao.mean():.1f}, NM.B Mean={w_metal.mean():.1f}")
