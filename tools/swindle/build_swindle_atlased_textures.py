import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

SRC_TEX_DIR = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Swindle\02_textures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Swindle\Textures")
UNITY_TEX_DIR.mkdir(parents=True, exist_ok=True)


def find_tex(name: str):
    if not name:
        return None
    p = SRC_TEX_DIR / name
    if p.exists():
        return p
    low = name.lower()
    for f in SRC_TEX_DIR.iterdir():
        if f.name.lower() == low:
            return f
    return None


def load_rgb(name: str, size, default_rgb=(80, 85, 75)) -> np.ndarray:
    fp = find_tex(name)
    if fp:
        im = Image.open(fp).convert("RGB")
        if im.size != size:
            im = im.resize(size, Image.Resampling.LANCZOS)
        return np.array(im, dtype=np.uint8)
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :] = default_rgb
    return arr


def load_normal_gl(name: str, size) -> np.ndarray:
    """Load DirectX normal map and flip G channel (G = 255 - G) to OpenGL standard."""
    fp = find_tex(name)
    if not fp:
        arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        arr[:, :] = (128, 128, 255)
        return arr
    im = Image.open(fp).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.uint8)
    arr[:, :, 1] = 255 - arr[:, :, 1]
    return arr


def load_em_mask(name: str, size, thresh=24) -> tuple[np.ndarray, np.ndarray]:
    """Return (rgb_em, scalar_mask_0_255)."""
    fp = find_tex(name)
    if not fp:
        z3 = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        z1 = np.zeros((size[1], size[0]), dtype=np.uint8)
        return z3, z1
    im = Image.open(fp).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.float32)
    lum = arr.max(axis=2)
    mask = np.clip((lum - thresh) / max(1.0, 180.0 - thresh), 0.0, 1.0)
    return arr.astype(np.uint8), (mask * 255.0).astype(np.uint8)


def boost_diffuse_with_em(diff_arr: np.ndarray, em_rgb: np.ndarray, em_mask: np.ndarray, is_head: bool) -> np.ndarray:
    """Boost diffuse color where emissive mask is active so eyes/conduits glow crisply."""
    out = diff_arr.astype(np.float32)
    m = (em_mask.astype(np.float32) / 255.0)[..., None]
    if is_head:
        # Vivid Decepticon ruby-purple visor glow
        target = np.array([240.0, 60.0, 255.0], dtype=np.float32)
        out = out * (1.0 - m) + target * m
    else:
        # Boost Decepticon purple emissive hue
        er = em_rgb.astype(np.float32)
        em_max = np.maximum(er.max(axis=2, keepdims=True), 1.0)
        vivid = np.clip((er / em_max) * 250.0, 0.0, 255.0)
        out = out * (1.0 - m * 0.85) + vivid * (m * 0.85)
    return np.clip(out, 0, 255).astype(np.uint8)


def make_decepticon_tile(size) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build (diff, norm_gl, em_mask, metallic_mask) for TR_FactionLogo_Mat_INST."""
    w, h = size
    diff = np.zeros((h, w, 3), dtype=np.uint8)
    diff[:, :] = (55, 52, 42)  # Swindle desert-tan / gunmetal backing plate
    fp = find_tex("DecepticonLogo.png")
    em_mask = np.zeros((h, w), dtype=np.uint8)
    if fp:
        logo = Image.open(fp).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        la = np.array(logo, dtype=np.float32)
        alpha = la[:, :, 3:4] / 255.0
        logo_rgb = la[:, :, :3]
        lum = logo_rgb.mean(axis=2, keepdims=True)
        tinted = np.clip(np.concatenate([lum * 0.95 + 40, lum * 0.40 + 10, lum * 1.05 + 50], axis=2), 0, 255)
        diff = np.clip(diff.astype(np.float32) * (1.0 - alpha) + tinted * alpha, 0, 255).astype(np.uint8)
        em_mask = np.clip((alpha[:, :, 0] * (lum[:, :, 0] > 90) * 110), 0, 255).astype(np.uint8)
    norm_gl = np.zeros((h, w, 3), dtype=np.uint8)
    norm_gl[:, :] = (128, 128, 255)
    return diff, norm_gl, em_mask, np.full((h, w), 95, dtype=np.uint8)


def compute_kabam_pbr_channels(diff_arr: np.ndarray, norm_gl: np.ndarray, em_mask: np.ndarray):
    """Build Kabam (Nx, Ny, Metallic, 255) normal and 3-channel RGB RAOE."""
    df = diff_arr.astype(np.float32)
    dmax = df.max(axis=2)
    dmin = df.min(axis=2)
    lum = df.mean(axis=2)
    sat = (dmax - dmin) / np.maximum(dmax, 1.0)

    # Bare gunmetal chassis/joints vs painted desert sand armor
    is_bare_metal = (lum < 110.0) & (sat < 0.25) & (em_mask < 30)
    metallic = np.where(is_bare_metal, 110.0, 25.0)
    metallic = np.where(em_mask >= 30, 0.0, metallic)

    # Roughness (R): matte desert paint ~195 (0.76), bare metal ~152 (0.60)
    rough = np.where(is_bare_metal, 155.0, 195.0)
    # Soft cavity AO (G) from albedo luminance floor [205..255]
    ao = np.clip(205.0 + (lum / 255.0) * 50.0, 205.0, 255.0)

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

    # Unity Standard Preview Emission Map (RGB)
    em_factor = (em_mask.astype(np.float32) / 255.0)[..., None]
    unity_em = np.clip(df * em_factor * 1.25, 0, 255).astype(np.uint8)
    return nm_kabam, raoe, unity_em


def assemble_tile(diff_name, norm_name, em_name, size, is_head=False, em_thresh=24):
    d = load_rgb(diff_name, size)
    n = load_normal_gl(norm_name, size)
    em_rgb, em_m = load_em_mask(em_name, size, thresh=em_thresh)
    if em_m.max() > 0:
        d = boost_diffuse_with_em(d, em_rgb, em_m, is_head=is_head)
    return d, n, em_m


def build_atlas(tiles_spec, prefix):
    """tiles_spec: list of ((x, y, w, h), (diff, norm_gl, em_mask))."""
    diff_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)
    em_mask_atlas = np.zeros((2048, 2048), dtype=np.uint8)

    for (x, y, w, h), (d, n, em_m) in tiles_spec:
        diff_atlas[y:y+h, x:x+w] = d
        norm_unity_atlas[y:y+h, x:x+w] = n
        em_mask_atlas[y:y+h, x:x+w] = em_m

    nm_kabam, raoe_rgb, unity_em = compute_kabam_pbr_channels(diff_atlas, norm_unity_atlas, em_mask_atlas)

    em_pct = (raoe_rgb[:, :, 2] > 20).mean() * 100.0
    print(f"  [{prefix}] RAOE mode=RGB, RoughMean={raoe_rgb[:,:,0].mean():.1f}, EmissivePixels(>20)={em_pct:.2f}%, NM.B Mean={nm_kabam[:,:,2].mean():.1f}")

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


def main():
    print("=== [Swindle] Building Production 2048x2048 PBR Texture Atlases (OpenGL NM + NM.B + RGB RAOE) ===")

    # Robot Atlas (8 material slots, zero overlap):
    #   Q0 (0,0,1024,1024)       : Chest        U=[0.00, 0.50], V=[0.50, 1.00]
    #   Q1 (1024,0,1024,1024)    : Bazooka      U=[0.50, 1.00], V=[0.50, 1.00]
    #   Q2 (0,1024,1024,1024)    : Legs         U=[0.00, 0.50], V=[0.00, 0.50]
    #   Q3A (1024,1024,512,512)  : Head         U=[0.50, 0.75], V=[0.25, 0.50]
    #   Q3B (1536,1024,512,512)  : ArmLo        U=[0.75, 1.00], V=[0.25, 0.50]
    #   Q3C (1024,1536,512,512)  : ArmUp/Caps   U=[0.50, 0.75], V=[0.00, 0.25]
    #   Q3D_L (1536,1536,256,512): Wheel        U=[0.75, 0.875], V=[0.00, 0.25]
    #   Q3D_R (1792,1536,256,512): FactionLogo  U=[0.875, 1.00], V=[0.00, 0.25]
    d_logo_r, n_logo_r, em_logo_r, _ = make_decepticon_tile((256, 512))
    robot_tiles = [
        ((0, 0, 1024, 1024), assemble_tile("rb_swindle_chest_inst.jpg", "rb_swindle_chest_n.jpg", "chest_e.jpg", (1024, 1024))),
        ((1024, 0, 1024, 1024), assemble_tile("wep_bazooka_matinst.jpg", "wep_bazooka_n.jpg", "wep_bazooka_e.jpg", (1024, 1024))),
        ((0, 1024, 1024, 1024), assemble_tile("rb_swindle_legs_inst.jpg", "rb_swindle_legs_n.jpg", "legs_e.jpg", (1024, 1024))),
        ((1024, 1024, 512, 512), assemble_tile("rb_swindle_head_inst.jpg", "rb_swindle_head_n.jpg", "head_e.jpg", (512, 512), is_head=True)),
        ((1536, 1024, 512, 512), assemble_tile("rb_swindle_armlo_inst.jpg", "rb_swindle_armlo_n.jpg", "armlo_e.jpg", (512, 512))),
        ((1024, 1536, 512, 512), assemble_tile("rb_swindle_armup_inst.jpg", "rb_swindle_armup_n.jpg", "armup_e.jpg", (512, 512))),
        ((1536, 1536, 256, 512), assemble_tile("rb_swindle_wheel_inst.jpg", "rb_swindle_wheel_n.jpg", "wheels_e.jpg", (256, 512))),
        ((1792, 1536, 256, 512), (d_logo_r, n_logo_r, em_logo_r)),
    ]
    build_atlas(robot_tiles, "cha_swindle_main")

    # Vehicle Atlas (4 material slots, zero overlap):
    #   Q0 (0,0,1024,1024)       : Jeep Body (Main) U=[0.00, 0.50], V=[0.50, 1.00]
    #   Q1 (1024,0,1024,1024)    : Jeep Body (Duplicate/Mirror tile) U=[0.50, 1.00], V=[0.50, 1.00]
    #   Q2 (0,1024,1024,1024)    : Jeep Wheels      U=[0.00, 0.50], V=[0.00, 0.50]
    #   Q3 (1024,1024,1024,1024) : FactionLogo      U=[0.50, 1.00], V=[0.00, 0.50]
    d_logo_v, n_logo_v, em_logo_v, _ = make_decepticon_tile((1024, 1024))
    veh_tiles = [
        ((0, 0, 1024, 1024), assemble_tile("vh_swindle_cust_e_mat_inst.jpg", "vh_swindle_cust_e_mat_n.jpg", "vh_swindle_cust_e_mat_e.jpg", (1024, 1024))),
        ((1024, 0, 1024, 1024), assemble_tile("vh_swindle_cust_e_mat_inst.jpg", "vh_swindle_cust_e_mat_n.jpg", "vh_swindle_cust_e_mat_e.jpg", (1024, 1024))),
        ((0, 1024, 1024, 1024), assemble_tile("rb_swindle_wheel_inst.jpg", "rb_swindle_wheel_n.jpg", "wheels_e.jpg", (1024, 1024))),
        ((1024, 1024, 1024, 1024), (d_logo_v, n_logo_v, em_logo_v)),
    ]
    build_atlas(veh_tiles, "cha_swindle_tform_misc")
    print("[✓] All Swindle PBR textures built cleanly!")


if __name__ == "__main__":
    main()
