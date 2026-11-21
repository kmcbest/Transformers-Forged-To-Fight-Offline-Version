import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "StarSaber" / "textures"
OUT_DIR = ROOT / "3rd-party-models" / "StarSaber" / "02_textures"
UNITY_TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "StarSaber" / "Textures"

for d in (OUT_DIR, UNITY_TEX_DIR):
    d.mkdir(parents=True, exist_ok=True)


def load_normal_gl(path: Path, size) -> np.ndarray:
    """Load normal map, flip G (Y axis) from DirectX to OpenGL, resize to size."""
    im = Image.open(path).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.uint8)
    # Flip G for OpenGL
    arr[:, :, 1] = 255 - arr[:, :, 1]
    return arr


def compute_saturation(rgb: np.ndarray) -> np.ndarray:
    """Compute HSV saturation in [0, 1] for RGB array."""
    f = rgb.astype(np.float32) / 255.0
    cmax = f.max(axis=2)
    cmin = f.min(axis=2)
    return np.where(cmax > 1e-4, (cmax - cmin) / np.maximum(cmax, 1e-4), 0.0)


def process_body_textures():
    print("\n--- Processing Star Saber Robot Body Textures (2048x2048) ---")
    size = (2048, 2048)
    W, H = size

    # 1. Diffuse & eye Alpha (MUST convert to RGB and split L-channel Alpha BEFORE resize,
    #    otherwise Pillow RGBA LANCZOS premultiplies RGB by Alpha=0 and wipes texture black!)
    d_path = SRC_DIR / "Tx_StarSaber_D.png"
    im_d_src = Image.open(d_path)
    diff_arr = np.array(im_d_src.convert("RGB").resize(size, Image.Resampling.LANCZOS), dtype=np.uint8)
    alpha_im = im_d_src.getchannel("A").resize(size, Image.Resampling.LANCZOS)
    alpha_src = np.array(alpha_im, dtype=np.float32)

    # 2. Normal OpenGL
    n_path = SRC_DIR / "Tx_StarSaber_N.png"
    norm_gl = load_normal_gl(n_path, size)

    # 3. Specular / AO Mask (S.R=metal/edge wear, S.G=roughness, S.B=crisp cavity AO)
    s_path = SRC_DIR / "Tx_StarSaber_S.png"
    im_s = Image.open(s_path).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    s_arr = np.array(im_s, dtype=np.float32)
    s_r = s_arr[:, :, 0]
    s_b = s_arr[:, :, 2]

    # Emissive mask extraction:
    # Restrict strictly to verified eye/visor Alpha region inside head UV box (px_x=[225..269], y=[16..119] at 1K)
    # so ZERO cyan/gold/blue body armor ever leaks glow (prevents White Supernova HDR blow-out).
    head_roi = np.zeros((H, W), dtype=bool)
    head_roi[int(H * 0.01):int(H * 0.14), int(W * 0.21):int(W * 0.28)] = True

    visor_mask = head_roi & (alpha_src >= 10.0)
    em_vals = np.clip((alpha_src - 8.0) * 2.2, 0.0, 255.0)
    em_mask = np.where(visor_mask, em_vals, 0.0).astype(np.uint8)

    # Brighten visor RGB in Diffuse (original visor pixels have dark RGB ~48 behind Alpha glow)
    visor_core = head_roi & (alpha_src >= 40.0)
    diff_arr[visor_core] = np.array([150, 230, 255], dtype=np.uint8)

    em_f = (em_mask.astype(np.float32) / 255.0)[..., None]
    em_pct = (em_mask > 20).mean() * 100.0
    print(f"  Emissive pixels ratio: {em_pct:.3f}% (contract requires 0.05%..20.0%, target <2%)")

    # 4. Metallic & Roughness for Kabam standard:
    # Painted white, red, blue, and yellow armor -> NM.B = 0 (strict dielectric per §8.5/§11.10).
    df = diff_arr.astype(np.float32)
    lum = df.mean(axis=2)
    sat = compute_saturation(diff_arr)

    is_dark_metal = (sat < 0.22) & (lum >= 38.0) & (lum <= 125.0) & (~visor_mask)
    is_painted_armor = ~is_dark_metal

    metallic = np.zeros((H, W), dtype=np.float32)
    metal_detail = np.clip(85.0 + (s_r / 255.0) * 40.0, 85.0, 125.0)
    metallic = np.where(is_dark_metal, metal_detail, metallic)
    metallic = np.where(em_mask >= 20, 0.0, metallic)

    # Roughness: matte-satin ceramic/paint ~192, dark metal ~155, emissive ~130
    roughness = np.full((H, W), 192.0, dtype=np.float32)
    roughness = np.where(is_dark_metal, 155.0, roughness)
    roughness = np.where(em_mask >= 20, 130.0, roughness)

    # Cavity AO (G) from crisp source AO map (S.B)
    ao = np.clip(95.0 + (s_b / 255.0) * 160.0, 95.0, 255.0)

    # Build RAOE (strict RGB)
    raoe_rgb = np.stack([
        roughness.astype(np.uint8),
        ao.astype(np.uint8),
        em_mask.astype(np.uint8),
    ], axis=2)

    # Build Kabam Normal (Nx, Ny, Metallic)
    nm_kabam = np.stack([
        norm_gl[:, :, 0],
        norm_gl[:, :, 1],
        metallic.astype(np.uint8),
    ], axis=2)

    # Unity standard normal (Nz = 255)
    norm_unity = np.stack([
        norm_gl[:, :, 0],
        norm_gl[:, :, 1],
        np.full((H, W), 255, dtype=np.uint8),
    ], axis=2)

    # Unity Emission RGB (eyes/visor only)
    unity_em = np.clip(diff_arr.astype(np.float32) * em_f * 1.4, 0, 255).astype(np.uint8)

    prefix = "cha_starsaber_main"
    outputs = {
        f"{prefix}_Diffuse.png": Image.fromarray(diff_arr, "RGB"),
        f"{prefix}_Normal.png": Image.fromarray(nm_kabam, "RGB"),
        f"{prefix}_Normal_unity.png": Image.fromarray(norm_unity, "RGB"),
        f"{prefix}_RAOE.png": Image.fromarray(raoe_rgb, "RGB"),
        f"{prefix}_Emission.png": Image.fromarray(unity_em, "RGB"),
    }
    for d in (OUT_DIR, UNITY_TEX_DIR):
        for fname, im in outputs.items():
            im.save(d / fname)
    print(f"  [✓] Body textures saved. Painted={100*is_painted_armor.mean():.1f}% (NM.B=0), RoughMean={roughness.mean():.1f}, NM.B Mean={metallic.mean():.1f}")


def process_weapon_textures():
    print("\n--- Processing Star Saber Sword Textures (512x512) ---")
    size = (512, 512)
    W, H = size

    d_path = SRC_DIR / "Tx_StarSaber_Weapon_D.png"
    im_d = Image.open(d_path).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    diff_arr = np.array(im_d, dtype=np.uint8)

    n_path = SRC_DIR / "Tx_StarSaber_Weapon_N.png"
    norm_gl = load_normal_gl(n_path, size)

    s_path = SRC_DIR / "Tx_StarSaber_Weapon_S.png"
    s_arr = np.array(Image.open(s_path).convert("RGB").resize(size, Image.Resampling.LANCZOS), dtype=np.float32)
    s_r = s_arr[:, :, 0]
    s_b = s_arr[:, :, 2]

    df = diff_arr.astype(np.float32)
    lum = df.mean(axis=2)
    sat = compute_saturation(diff_arr)

    # Emissive mask: ONLY tiny hilt core accent (~0.10%) so white blade & red guard stay crisp non-emissive
    em_mask = np.zeros((H, W), dtype=np.uint8)
    slot_roi = np.zeros((H, W), dtype=bool)
    slot_roi[int(H * 0.85):int(H * 0.96), int(W * 0.48):int(W * 0.58)] = True
    gem_core = slot_roi & (s_arr[:, :, 1] < 50.0) & (s_arr[:, :, 2] > 180.0)
    if gem_core.sum() < 160:
        cy0, cy1 = int(H * 0.89), int(H * 0.89) + 16
        cx0, cx1 = int(W * 0.52), int(W * 0.52) + 16
        em_mask[cy0:cy1, cx0:cx1] = 180
    else:
        em_mask[gem_core] = 180
    em_pct = (em_mask > 20).mean() * 100.0
    print(f"  Emissive pixels ratio: {em_pct:.3f}%")

    # Metallic: painted red/blue guard & bright white shield panels stay dielectric (NM.B=0);
    # neutral steel blade (lum 115..178) & dark hilt grip (lum 35..115) keep metallic sheen
    is_neutral = sat < 0.18
    is_steel_blade = is_neutral & (lum >= 115.0) & (lum <= 178.0) & (s_r >= 90.0)
    is_dark_metal = is_neutral & (lum >= 35.0) & (lum < 115.0)

    metallic = np.zeros((H, W), dtype=np.float32)
    metallic = np.where(is_steel_blade, 115.0, metallic)
    metallic = np.where(is_dark_metal, 95.0, metallic)
    metallic = np.where(em_mask >= 20, 0.0, metallic)

    # Roughness: painted panels ~185, steel blade ~145, dark grip ~165
    roughness = np.full((H, W), 185.0, dtype=np.float32)
    roughness = np.where(is_steel_blade, 145.0, roughness)
    roughness = np.where(is_dark_metal, 165.0, roughness)
    roughness = np.where(em_mask >= 20, 130.0, roughness)

    # AO from crisp Weapon_S.B
    ao = np.clip(95.0 + (s_b / 255.0) * 160.0, 95.0, 255.0)

    raoe_rgb = np.stack([
        roughness.astype(np.uint8),
        ao.astype(np.uint8),
        em_mask.astype(np.uint8),
    ], axis=2)

    nm_kabam = np.stack([
        norm_gl[:, :, 0],
        norm_gl[:, :, 1],
        metallic.astype(np.uint8),
    ], axis=2)

    norm_unity = np.stack([
        norm_gl[:, :, 0],
        norm_gl[:, :, 1],
        np.full((H, W), 255, dtype=np.uint8),
    ], axis=2)

    em_f = (em_mask.astype(np.float32) / 255.0)[..., None]
    unity_em = np.clip(diff_arr.astype(np.float32) * em_f * 1.2, 0, 255).astype(np.uint8)

    prefix = "cha_starsaber_wpns"
    outputs = {
        f"{prefix}_Diffuse.png": Image.fromarray(diff_arr, "RGB"),
        f"{prefix}_Normal.png": Image.fromarray(nm_kabam, "RGB"),
        f"{prefix}_Normal_unity.png": Image.fromarray(norm_unity, "RGB"),
        f"{prefix}_RAOE.png": Image.fromarray(raoe_rgb, "RGB"),
        f"{prefix}_Emission.png": Image.fromarray(unity_em, "RGB"),
    }
    for d in (OUT_DIR, UNITY_TEX_DIR):
        for fname, im in outputs.items():
            im.save(d / fname)
    print(f"  [✓] Weapon textures saved. RoughMean={roughness.mean():.1f}, NM.B Mean={metallic.mean():.1f}")


if __name__ == "__main__":
    process_body_textures()
    process_weapon_textures()
    print("\n[✓] All Star Saber PBR textures built successfully!")
