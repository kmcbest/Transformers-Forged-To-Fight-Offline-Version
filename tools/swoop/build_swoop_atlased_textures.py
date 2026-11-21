import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import colorsys
import numpy as np
from PIL import Image

SRC_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\textures")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\02_textures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Swoop\Textures")
UNITY_TEX_DIR.mkdir(parents=True, exist_ok=True)


def load_rgb(fname, size) -> np.ndarray:
    p = SRC_DIR / fname
    im = Image.open(p).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    return np.array(im, dtype=np.uint8)


def load_normal_gl(fname, size) -> np.ndarray:
    """Load DirectX normal map and flip Green channel (G = 255 - G) to OpenGL standard."""
    p = SRC_DIR / fname
    im = Image.open(p).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.uint8)
    arr[:, :, 1] = 255 - arr[:, :, 1]
    return arr


def rgb_to_hsv_np(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    f = rgb.astype(np.float32) / 255.0
    r, g, b = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    h = np.zeros_like(cmax)
    mask = delta > 1e-6
    rm = mask & (cmax == r)
    gm = mask & (cmax == g)
    bm = mask & (cmax == b)
    h[rm] = ((g[rm] - b[rm]) / delta[rm]) % 6.0
    h[gm] = ((b[gm] - r[gm]) / delta[gm]) + 2.0
    h[bm] = ((r[bm] - g[bm]) / delta[bm]) + 4.0
    h = (h / 6.0) % 1.0

    s = np.where(cmax > 1e-6, delta / np.maximum(cmax, 1e-6), 0.0)
    v = cmax
    return h, s, v


def hsv_to_rgb_np(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> np.ndarray:
    i = np.floor(h * 6.0).astype(np.int32)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i6 = i % 6

    r = np.choose(i6, [v, q, p, p, t, v])
    g = np.choose(i6, [t, v, v, q, p, p])
    b = np.choose(i6, [p, p, t, v, v, q])
    return np.clip(np.stack([r, g, b], axis=2) * 255.0, 0.0, 255.0).astype(np.uint8)


def calibrate_swoop_albedo(rgb: np.ndarray, s_ao: np.ndarray) -> np.ndarray:
    """
    Grimlock-grade vivid metallic Dinobot albedo:
    - Preserves black crevices & panel gaps (no washed-out lifted blacks!)
    - Boosts color saturation (1.42x) so blue/red/gold pop crisply instead of chalky pastel
    - Uses gentle midtone lift + authored AO shading so colors stay rich under Kabam exposure
    """
    h, s, v = rgb_to_hsv_np(rgb)

    # Boost chromatic saturation cleanly while leaving neutral grey/silver neutral
    color_mask = np.clip((s - 0.12) / 0.18, 0.0, 1.0)
    s_new = np.clip(s * (1.0 + 0.45 * color_mask), 0.0, 0.96)

    # Contrast-preserving luminance lift: protect crevices (v < 0.14), moderately boost armor (0.25..0.75)
    t_prot = np.clip((v - 0.08) / 0.16, 0.0, 1.0)
    t_prot = t_prot * t_prot * (3.0 - 2.0 * t_prot)
    v_lifted = np.power(np.maximum(v, 1e-4), 0.72) * 1.06
    v_new = v + (v_lifted - v) * t_prot

    # Apply subtle baked AO contrast from Tx_Swoop_S.B so panel seams stay deep and crisp
    ao_norm = np.clip(s_ao.astype(np.float32) / 255.0, 0.0, 1.0)
    v_new = np.clip(v_new * (0.72 + 0.32 * ao_norm), 0.0, 0.96)

    return hsv_to_rgb_np(h, s_new, v_new)


def make_autobot_split_tile(size=(512, 512)) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create 2-zone 512x512 Emblem UV tile [1536:2048, 512:1024]:
    - Top half    (y=[0:256],   UV V=[0.625..0.750]): Deep Crimson Red for M_Swoop_Emblem (SubMesh 1, em=200)
    - Bottom half (y=[256:512], UV V=[0.500..0.625]): Dark Gunmetal Shield for M_Symbol_Black (SubMesh 0, em=0)
    """
    w, h = size
    diff = np.zeros((h, w, 3), dtype=np.uint8)
    diff[0 : h // 2, :] = (225, 12, 12)   # Deep rich crimson Autobot crest (no pastel white-pink blow-out!)
    diff[h // 2 : h, :] = (34, 38, 44)    # Dark gunmetal shield backing plate

    norm = np.zeros((h, w, 3), dtype=np.uint8)
    norm[:, :] = (128, 128, 255)

    em_m = np.zeros((h, w), dtype=np.uint8)
    em_m[0 : h // 2, :] = 200
    return diff, norm, em_m


def compute_swoop_pbr_channels(diff_arr: np.ndarray, norm_gl: np.ndarray, s_atlas: np.ndarray, em_mask: np.ndarray):
    """
    Compute Kabam PBR channels calibrated directly against official Grimlock (`grimlock_gs_mp08`):
      - Grimlock NM.B (Metallic): mean ~143..214 (strong metallic reflections!)
      - Grimlock RAOE.R (Roughness): mean ~59 (p10=24, p50=65, p90=106 -> sleek metallic gleam!)
      - Grimlock RAOE.G (AO): mean ~197 (p10=72, p50=226 -> crisp crevice contrast!)
    """
    df = diff_arr.astype(np.float32)
    dmax = df.max(axis=2)
    dmin = df.min(axis=2)
    lum = df.mean(axis=2)
    sat = (dmax - dmin) / np.maximum(dmax, 1.0)

    sr = s_atlas[:, :, 0].astype(np.float32)   # Authored metallic/spec intensity
    sg = s_atlas[:, :, 1].astype(np.float32)   # Authored gloss/roughness clue
    sb = s_atlas[:, :, 2].astype(np.float32)   # Authored AO

    is_crevice = lum < 32.0
    is_dark_frame = (lum < 95.0) & (sat < 0.22) & (~is_crevice)
    is_silver = (lum >= 105.0) & (sat < 0.16)
    is_gold = (df[:, :, 0] > 110.0) & (df[:, :, 1] > 90.0) & (df[:, :, 2] < 85.0)

    # 1. Metallic Mask (NM.B): target mean ~165 (Grimlock-grade real metal!)
    metallic = np.full(df.shape[:2], 155.0, dtype=np.float32)  # Painted metallic blue/red Dinobot armor
    metallic[is_dark_frame] = 140.0                            # Dark gunmetal chassis
    metallic[is_gold] = 225.0                                  # Brassy metallic Dinobot gold
    metallic[is_silver] = 220.0                                # Crisp brushed silver wings/face
    metallic = np.clip(metallic * (0.75 + 0.35 * (sr / 255.0)), 60.0, 248.0)
    metallic[is_crevice] = 35.0                                # Matte recessed panel seams
    metallic[em_mask >= 40] = 0.0                              # Emissive optics are dielectric

    # 2. Roughness (RAOE.R): target mean ~60 matching Grimlock (59.2)!
    rough = np.full(df.shape[:2], 64.0, dtype=np.float32)      # Painted glossy metallic armor
    rough[is_dark_frame] = 82.0                                # Slightly rougher gunmetal frame
    rough[is_gold] = 46.0                                      # Sleek polished Dinobot gold
    rough[is_silver] = 48.0                                    # Crisp metallic silver wings/face
    # Modulate slightly with inverse authored specular so scuffs/highlights read cleanly
    rough = np.clip(rough + (115.0 - sg) * 0.18, 28.0, 125.0)
    rough[is_crevice] = 140.0
    rough[em_mask >= 40] = 30.0

    # 3. Ambient Occlusion (RAOE.G): target mean ~197, p10 ~75 matching Grimlock (197.1)!
    sb_norm = np.clip(sb / 255.0, 0.0, 1.0)
    lum_ao = np.clip((lum - 12.0) / 80.0, 0.25, 1.0)
    ao = np.clip(255.0 * np.power(sb_norm, 1.7) * (0.55 + 0.45 * lum_ao), 45.0, 255.0)

    raoe = np.stack([
        rough.astype(np.uint8),
        ao.astype(np.uint8),
        em_mask.astype(np.uint8),
    ], axis=2)

    nm_kabam = np.stack([
        norm_gl[:, :, 0],
        norm_gl[:, :, 1],
        metallic.astype(np.uint8),
    ], axis=2)

    em_factor = (em_mask.astype(np.float32) / 255.0)[..., None]
    unity_em = np.clip(df * em_factor * 1.5, 0, 255).astype(np.uint8)
    return nm_kabam, raoe, unity_em


def build_swoop_atlas():
    print("=== [Swoop] Building Grimlock-Calibrated 2048x2048 PBR Atlases (Real Eyes Only + Metallic Gloss) ===")

    diff_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)
    s_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    s_atlas[:, :] = (140, 105, 240)
    em_mask_atlas = np.zeros((2048, 2048), dtype=np.uint8)

    # 1. Load raw Body textures at 1536x1536 (1.5x of 1024x1024 source)
    raw_body_d = load_rgb("Tx_Swoop_D_RGB.png", (1536, 1536))
    body_n = load_normal_gl("Tx_Swoop_N.png", (1536, 1536))
    body_s = load_rgb("Tx_Swoop_S.png", (1536, 1536))

    # Build pinpoint REAL Eye Masks on raw 1536x1536 coords (verified 100% from 3D mesh + Tx_Swoop_D Alpha!):
    # A. Real Robot Eyes (below brow! Z=[10.07, 10.08]): 1024x1024 x=[948..992], y=[638..652] -> 1536x1536 x=[1422..1488], y=[957..978]
    # B. Pteranodon Eyes (side of gold head crest):     1024x1024 x=[600..666], y=[5..34]    -> 1536x1536 x=[900..999], y=[8..51]
    # Note: Forehead brow (py=[650..674]) is explicitly EXCLUDED so it stays dark gunmetal!
    raw_max = raw_body_d.max(axis=2).astype(np.int32)
    raw_min = raw_body_d.min(axis=2).astype(np.int32)
    is_eye_dark = (raw_max < 55) & ((raw_max - raw_min) < 20)

    robot_eyes_roi = np.zeros((1536, 1536), dtype=bool)
    robot_eyes_roi[957:979, 1422:1489] = True

    bird_eyes_roi = np.zeros((1536, 1536), dtype=bool)
    bird_eyes_roi[8:52, 900:1000] = True

    eye_mask = is_eye_dark & (robot_eyes_roi | bird_eyes_roi)
    body_em = np.zeros((1536, 1536), dtype=np.uint8)
    body_em[eye_mask] = 245

    body_d = calibrate_swoop_albedo(raw_body_d, body_s[:, :, 2])
    body_d[eye_mask] = (35, 195, 255)

    print(f"  Raw Body mean lum={raw_body_d.mean():.1f} -> Calibrated Body mean lum={body_d.mean():.1f}")
    print(f"  Pinpoint REAL eye pixels: robot_eyes={(is_eye_dark & robot_eyes_roi).sum()}, bird_eyes={(is_eye_dark & bird_eyes_roi).sum()}")

    diff_atlas[0:1536, 0:1536] = body_d
    norm_unity_atlas[0:1536, 0:1536] = body_n
    s_atlas[0:1536, 0:1536] = body_s
    em_mask_atlas[0:1536, 0:1536] = body_em

    # 2. Load Weapon textures [y=0:512, x=1536:2048]
    raw_wpn_d = load_rgb("Tx_Swoop_Weapon_D_RGB.png", (512, 512))
    wpn_s = load_rgb("Tx_Swoop_Weapon_S.png", (512, 512))
    wpn_d = calibrate_swoop_albedo(raw_wpn_d, wpn_s[:, :, 2])
    wpn_n = load_normal_gl("Tx_Swoop_Weapon_N.png", (512, 512))

    diff_atlas[0:512, 1536:2048] = wpn_d
    norm_unity_atlas[0:512, 1536:2048] = wpn_n
    s_atlas[0:512, 1536:2048] = wpn_s

    # 3. Autobot Emblem 2-zone Split Tile [y=512:1024, x=1536:2048]
    ab_d, ab_n, ab_em = make_autobot_split_tile((512, 512))
    diff_atlas[512:1024, 1536:2048] = ab_d
    norm_unity_atlas[512:1024, 1536:2048] = ab_n
    em_mask_atlas[512:1024, 1536:2048] = ab_em
    s_atlas[512:768, 1536:2048] = (20, 140, 255)   # Enamel crest
    s_atlas[768:1024, 1536:2048] = (160, 105, 255) # Gunmetal plate

    # 4. Spare bottom strip [y=1536:2048, x=0:2048]
    diff_atlas[1536:2048, :] = (48, 52, 58)
    diff_atlas[1700:1850, :] = (195, 160, 45)
    norm_unity_atlas[1536:2048, :] = (128, 128, 255)

    # Compute Kabam PBR outputs
    nm_kabam, raoe_rgb, unity_em = compute_swoop_pbr_channels(diff_atlas, norm_unity_atlas, s_atlas, em_mask_atlas)

    em_pct = (raoe_rgb[:, :, 2] > 20).mean() * 100.0
    print(f"Atlas Stats (Target vs Grimlock R~59, AO~197, NMB~143..214):")
    print(f"  RAOE.R (Roughness) mean: {raoe_rgb[:, :, 0].mean():.1f}")
    print(f"  RAOE.G (AO)        mean: {raoe_rgb[:, :, 1].mean():.1f}, p10={np.percentile(raoe_rgb[:, :, 1], 10):.1f}")
    print(f"  Kabam NM.B (Metal) mean: {nm_kabam[:, :, 2].mean():.1f}")
    print(f"  Emissive pixels (>20): {em_pct:.2f}%")

    for prefix in ("cha_swoop_main", "cha_swoop_vh"):
        outputs = {
            f"{prefix}_Diffuse.png": Image.fromarray(diff_atlas, "RGB"),
            f"{prefix}_Normal.png": Image.fromarray(nm_kabam, "RGB"),
            f"{prefix}_Normal_unity.png": Image.fromarray(norm_unity_atlas, "RGB"),
            f"{prefix}_RAOE.png": Image.fromarray(raoe_rgb, "RGB"),
            f"{prefix}_Emission.png": Image.fromarray(unity_em, "RGB"),
        }
        for d in (OUT_DIR, UNITY_TEX_DIR):
            for fname, im in outputs.items():
                im.save(d / fname)
        print(f"[✓] Saved texture set for '{prefix}' to {OUT_DIR} and {UNITY_TEX_DIR}")


if __name__ == "__main__":
    build_swoop_atlas()
