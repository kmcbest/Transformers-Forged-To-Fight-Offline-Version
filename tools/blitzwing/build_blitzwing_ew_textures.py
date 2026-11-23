import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
OUT_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Also sync directly to unity project and 02_textures
UNITY_TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Textures"
UNITY_TEX_DIR.mkdir(parents=True, exist_ok=True)
STAGE_TEX_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "02_textures"
STAGE_TEX_DIR.mkdir(parents=True, exist_ok=True)

def load_rgba(name: str, size=(1024, 1024)) -> Image.Image:
    p = SRC_DIR / name
    assert p.exists(), f"Missing texture: {p}"
    im = Image.open(p)
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    return im

def process_tile_channels(t_name, n_name, arm_name, is_robot=True, is_head=False, is_vehicle=False):
    """
    Reads _T (Albedo), _N (Normal), and _ARM (AO, Roughness, Metallic)
    Returns:
      diff_rgb: uint8 (H, W, 3)
      norm_gl: uint8 (H, W, 3) with Nz=255
      norm_kabam: uint8 (H, W, 3) with B=Metallic
      raoe_rgb: uint8 (H, W, 3) with R=Rough, G=AO, B=Emissive
      em_rgb: uint8 (H, W, 3) for Unity preview
    """
    im_t = load_rgba(t_name)
    im_n = load_rgba(n_name)
    im_arm = load_rgba(arm_name)

    t_arr = np.array(im_t)
    n_arr = np.array(im_n.convert("RGB"))
    arm_arr = np.array(im_arm.convert("RGB"))

    # 1. Albedo
    diff_rgb = t_arr[:, :, :3].copy()

    # 2. Normal Map: DirectX -> OpenGL (flip Y/Green channel: G = 255 - G)
    norm_gl = n_arr.copy()
    norm_gl[:, :, 1] = 255 - norm_gl[:, :, 1]
    norm_gl[:, :, 2] = 255  # Unity standard Nz = 255

    # 3. Emissive Mask
    em_mask = np.zeros(diff_arr_shape := diff_rgb.shape[:2], dtype=np.uint8)
    if is_head:
        # Red visor on robot head
        is_red_visor = (diff_rgb[:, :, 0] > 155) & (diff_rgb[:, :, 1] < 75) & (diff_rgb[:, :, 2] < 75)
        em_mask[is_red_visor] = 255
        # Boost diffuse on visor so it glows intensely
        diff_rgb[is_red_visor] = np.array([255, 30, 30], dtype=np.uint8)
    elif is_vehicle:
        # Red canopy / glass
        if t_arr.ndim == 3 and t_arr.shape[2] == 4:
            is_canopy = (t_arr[:, :, 3] < 252) | ((diff_rgb[:, :, 0] > 130) & (diff_rgb[:, :, 1] < 60) & (diff_rgb[:, :, 2] < 60))
        else:
            is_canopy = (diff_rgb[:, :, 0] > 130) & (diff_rgb[:, :, 1] < 60) & (diff_rgb[:, :, 2] < 60)
        em_mask[is_canopy] = 255
        diff_rgb[is_canopy] = np.array([245, 40, 40], dtype=np.uint8)

    # 4. Roughness (RAOE.R):
    # ARM.G is Roughness. Map to [145..210] to avoid greasy mirror shine in Kabam shader.
    raw_rough = arm_arr[:, :, 1].astype(np.float32)
    rough = np.clip(145.0 + (raw_rough / 255.0) * 60.0, 140.0, 215.0).astype(np.uint8)

    # 5. AO (RAOE.G):
    # ARM.R is AO. Soft cavity AO [195..255]
    raw_ao = arm_arr[:, :, 0].astype(np.float32)
    ao = np.clip(195.0 + (raw_ao / 255.0) * 55.0, 190.0, 255.0).astype(np.uint8)

    # 6. Metallic (Kabam Normal.B):
    # ARM.B is Metallic.
    # Where ARM.B is high or dark metal joints -> 115, painted armor -> 30
    raw_metal = arm_arr[:, :, 2].astype(np.float32)
    metallic = np.where(raw_metal > 120.0, 115.0, 32.0)
    # Zero metallic on emissive visor/glass
    metallic[em_mask > 20] = 0.0
    metallic = metallic.astype(np.uint8)

    # Construct Kabam Normal (Nx, Ny, Metallic)
    norm_kabam = np.stack([norm_gl[:, :, 0], norm_gl[:, :, 1], metallic], axis=2)

    # Construct strict RGB RAOE
    raoe_rgb = np.stack([rough, ao, em_mask], axis=2)

    # Construct Unity Emission map (RGB)
    em_factor = (em_mask.astype(np.float32) / 255.0)[..., None]
    unity_em = np.clip(diff_rgb.astype(np.float32) * em_factor * 1.2, 0, 255).astype(np.uint8)

    return diff_rgb, norm_gl, norm_kabam, raoe_rgb, unity_em

def build_robot_atlas():
    print("=== Building Robot Texture Atlas (2048x2048) ===")
    # M_a (Torso, Head, Wings) at Top-Left (0, 0, 1024, 1024)
    # M_b (Arms, Legs, Boots) at Bottom-Left (0, 1024, 1024, 1024)
    # W1 (Weapons: Gun & Sword) at Top-Right (1024, 0, 1024, 1024)
    # Bottom-Right (1024, 1024, 1024, 1024) neutral gunmetal backing
    
    diff_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)
    norm_kabam_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_kabam_atlas[:, :] = (128, 128, 30)
    raoe_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    raoe_atlas[:, :, 0] = 185  # default matte roughness
    raoe_atlas[:, :, 1] = 230  # default AO
    em_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)

    tiles = [
        # (x, y, w, h), t, n, arm, is_head, is_veh
        ((0, 0, 1024, 1024), "H_shandian_G1_M_a_T.png", "H_shandian_G1_M_a_N.png", "H_shandian_G1_M_a_ARM.png", True, False),
        ((0, 1024, 1024, 1024), "H_shandian_G1_M_b_T.png", "H_shandian_G1_M_b_N.png", "H_shandian_G1_M_b_ARM.png", False, False),
        ((1024, 0, 1024, 1024), "H_shandian_G1_W1_T.png", "H_shandian_G1_W1_N.png", "H_shandian_G1_W1_ARM.png", False, False),
    ]

    for (x, y, w, h), t_n, n_n, a_n, is_h, is_v in tiles:
        d, n_gl, n_k, r, em = process_tile_channels(t_n, n_n, a_n, is_robot=True, is_head=is_h, is_vehicle=is_v)
        # Resize W1 from 512 to 1024 if needed
        if d.shape[:2] != (h, w):
            d = np.array(Image.fromarray(d).resize((w, h), Image.Resampling.LANCZOS))
            n_gl = np.array(Image.fromarray(n_gl).resize((w, h), Image.Resampling.LANCZOS))
            n_k = np.array(Image.fromarray(n_k).resize((w, h), Image.Resampling.NEAREST))
            r = np.array(Image.fromarray(r).resize((w, h), Image.Resampling.NEAREST))
            em = np.array(Image.fromarray(em).resize((w, h), Image.Resampling.LANCZOS))

        diff_atlas[y:y+h, x:x+w] = d
        norm_unity_atlas[y:y+h, x:x+w] = n_gl
        norm_kabam_atlas[y:y+h, x:x+w] = n_k
        raoe_atlas[y:y+h, x:x+w] = r
        em_atlas[y:y+h, x:x+w] = em

    # Bottom-right backing plate (neutral dark chassis metal)
    diff_atlas[1024:, 1024:] = (45, 45, 48)
    norm_unity_atlas[1024:, 1024:] = (128, 128, 255)
    norm_kabam_atlas[1024:, 1024:] = (128, 128, 110)
    raoe_atlas[1024:, 1024:, 0] = 160
    raoe_atlas[1024:, 1024:, 1] = 220
    raoe_atlas[1024:, 1024:, 2] = 0

    save_outputs("cha_blitzwing_main", diff_atlas, norm_kabam_atlas, norm_unity_atlas, raoe_atlas, em_atlas)

def build_vehicle_atlas():
    print("\n=== Building Vehicle Texture Atlas (2048x2048) ===")
    # Tank (V1) at Top-Left (0, 0, 1024, 1024)
    # Jet (V2) at Top-Right (1024, 0, 1024, 1024)
    # Bottom half (0, 1024, 2048, 1024) neutral gunmetal backing
    
    diff_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)
    norm_kabam_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_kabam_atlas[:, :] = (128, 128, 30)
    raoe_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    raoe_atlas[:, :, 0] = 185
    raoe_atlas[:, :, 1] = 230
    em_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)

    tiles = [
        ((0, 0, 1024, 1024), "H_shandian_G1_V1_T.png", "H_shandian_G1_V1_N.png", "H_shandian_G1_V1_ARM.png", False, True),
        ((1024, 0, 1024, 1024), "H_shandian_G1_V2_T.png", "H_shandian_G1_V2_N.png", "H_shandian_G1_V2_ARM.png", False, True),
    ]

    for (x, y, w, h), t_n, n_n, a_n, is_h, is_v in tiles:
        d, n_gl, n_k, r, em = process_tile_channels(t_n, n_n, a_n, is_robot=False, is_head=is_h, is_vehicle=is_v)
        diff_atlas[y:y+h, x:x+w] = d
        norm_unity_atlas[y:y+h, x:x+w] = n_gl
        norm_kabam_atlas[y:y+h, x:x+w] = n_k
        raoe_atlas[y:y+h, x:x+w] = r
        em_atlas[y:y+h, x:x+w] = em

    diff_atlas[1024:, :] = (45, 45, 48)
    norm_unity_atlas[1024:, :] = (128, 128, 255)
    norm_kabam_atlas[1024:, :] = (128, 128, 110)
    raoe_atlas[1024:, :, 0] = 160
    raoe_atlas[1024:, :, 1] = 220
    raoe_atlas[1024:, :, 2] = 0

    save_outputs("cha_blitzwing_tform_misc", diff_atlas, norm_kabam_atlas, norm_unity_atlas, raoe_atlas, em_atlas)

def save_outputs(prefix, diff, norm_k, norm_u, raoe, em):
    em_pct = (raoe[:, :, 2] > 20).mean() * 100.0
    r_mean = raoe[:, :, 0].mean()
    nk_mean = norm_k[:, :, 2].mean()
    nu_mean = norm_u[:, :, 2].mean()
    print(f"  [{prefix}] RAOE=RGB (RoughMean={r_mean:.1f}, EmissivePct={em_pct:.2f}%), Kabam NM.B={nk_mean:.1f}, Unity NM.B={nu_mean:.1f}")

    # Validate gate assertions before saving
    assert 130.0 <= r_mean <= 235.0, f"Roughness mean {r_mean} out of range [130, 235]"
    assert 0.05 <= em_pct <= 20.0, f"Emissive pct {em_pct:.2f}% out of range [0.05, 20.0]"
    assert nk_mean < 195.0, f"Kabam NM.B {nk_mean} >= 195.0"
    assert nu_mean > 200.0, f"Unity NM.B {nu_mean} <= 200.0"

    files = {
        f"{prefix}_Diffuse.png": Image.fromarray(diff, "RGB"),
        f"{prefix}_Normal.png": Image.fromarray(norm_k, "RGB"),
        f"{prefix}_Normal_unity.png": Image.fromarray(norm_u, "RGB"),
        f"{prefix}_RAOE.png": Image.fromarray(raoe, "RGB"),
        f"{prefix}_Emission.png": Image.fromarray(em, "RGB"),
    }

    # Save to all required target directories
    for d in (OUT_DIR, UNITY_TEX_DIR, STAGE_TEX_DIR):
        for fname, im in files.items():
            im.save(d / fname)
            # If d == UNITY_TEX_DIR, also create alias matching Unity naming if needed
    print(f"  [SAVED] {prefix} 5 textures to OUT_DIR, UNITY_TEX_DIR, and STAGE_TEX_DIR.")

if __name__ == "__main__":
    build_robot_atlas()
    build_vehicle_atlas()
    print("\n[SUCCESS] Texture atlasing complete!")
