import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
OUT_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
UNITY_TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Textures"
STAGE_TEX_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "02_textures"
SWORD_POLYS_JSON = ROOT / "scratch" / "sword_polys_uv.json"

for d in (OUT_DIR, UNITY_TEX_DIR, STAGE_TEX_DIR):
    d.mkdir(parents=True, exist_ok=True)


def build_weapon_textures(size=(1024, 1024)):
    t_path = SRC_DIR / "H_shandian_G1_W1_T.png"
    n_path = SRC_DIR / "H_shandian_G1_W1_N.png"
    arm_path = SRC_DIR / "H_shandian_G1_W1_ARM.png"
    for p in (t_path, n_path, arm_path):
        assert p.exists(), f"Missing {p}"

    im_t = Image.open(t_path)
    im_n = Image.open(n_path)
    im_arm = Image.open(arm_path)
    print(f"[SRC] T={im_t.size} {im_t.mode}, N={im_n.size} {im_n.mode}, ARM={im_arm.size} {im_arm.mode}")

    if im_t.size != size:
        im_t = im_t.resize(size, Image.Resampling.LANCZOS)
    if im_n.size != size:
        im_n = im_n.resize(size, Image.Resampling.LANCZOS)
    if im_arm.size != size:
        im_arm = im_arm.resize(size, Image.Resampling.LANCZOS)

    diff_arr = np.array(im_t.convert("RGB"), dtype=np.float32)
    n_arr = np.array(im_n.convert("RGB"), dtype=np.uint8)
    arm_arr = np.array(im_arm.convert("RGB"), dtype=np.float32)

    # 1. Build Blade UV Mask (Z >= 2.15: cutting edges, blade faces, and tip; excludes hilt & guard)
    W, H = size
    blade_mask_img = Image.new("L", (W, H), 0)
    b_draw = ImageDraw.Draw(blade_mask_img)

    if SWORD_POLYS_JSON.exists():
        polys = json.loads(SWORD_POLYS_JSON.read_text(encoding="utf-8"))
        blade_polys = [p for p in polys if p["avg_z"] > 2.0]
        for p in blade_polys:
            pts = [(u * W, (1.0 - v) * H) for u, v in p["uv_pts"]]
            b_draw.polygon(pts, fill=255)
        print(f"[BLADE_MASK] Loaded {len(blade_polys)} blade polygons from {SWORD_POLYS_JSON.name}")
    else:
        print("[WARN] SWORD_POLYS_JSON not found, blade mask empty!")

    mask_arr = np.array(blade_mask_img, dtype=np.float32) / 255.0
    m3 = mask_arr[:, :, None]

    # Normal Map: DirectX -> OpenGL (flip G)
    norm_gl = n_arr.copy()
    norm_gl[:, :, 1] = 255 - norm_gl[:, :, 1]
    norm_gl[:, :, 2] = 255

    # Roughness: ARM.G -> [145..210], blade is smoother [85..110]
    raw_rough = arm_arr[:, :, 1]
    rough_default = np.clip(145.0 + (raw_rough / 255.0) * 60.0, 140.0, 215.0)
    rough_blade = np.clip(85.0 + (raw_rough / 255.0) * 25.0, 80.0, 115.0)
    rough = rough_default * (1.0 - mask_arr) + rough_blade * mask_arr
    rough = np.clip(rough, 0, 255).astype(np.uint8)

    # AO: ARM.R -> [195..255]
    raw_ao = arm_arr[:, :, 0]
    ao = np.clip(195.0 + (raw_ao / 255.0) * 55.0, 190.0, 255.0).astype(np.uint8)

    # Metallic: ARM.B -> 115 (metal on hilt/gun) vs 25 (dielectric crystal on glowing blade)
    raw_metal = arm_arr[:, :, 2]
    metallic_default = np.where(raw_metal > 120.0, 115.0, 32.0)
    metallic = metallic_default * (1.0 - mask_arr) + 25.0 * mask_arr
    metallic = np.clip(metallic, 0, 255).astype(np.uint8)

    norm_kabam = np.stack([norm_gl[:, :, 0], norm_gl[:, :, 1], metallic], axis=2)

    # Emissive (RAOE.B):
    # Onslaught gold standard: 220 ~ 255 on glowing blade, 0 on hilt/guard/gun
    dist = scipy.ndimage.distance_transform_edt(mask_arr > 0.5)
    em_val = (210.0 + np.clip(dist / 22.0, 0.0, 1.0) * 35.0) * mask_arr
    em_mask = np.clip(em_val, 0, 245).astype(np.uint8)
    raoe_rgb = np.stack([rough, ao, em_mask], axis=2)

    # Diffuse:
    # 3-stage gradient matching official G1/IDW Blitzwing character card:
    # - Cutting edge (dist -> 0): electric purple [175, 20, 255]
    # - Mid-blade halo (dist ~ 10): vivid neon magenta [225, 95, 255]
    # - Core spine (dist >= 22): blazing white-hot energon core [255, 245, 255]
    edge_col = np.array([175.0, 20.0, 255.0], dtype=np.float32)
    mid_col = np.array([225.0, 95.0, 255.0], dtype=np.float32)
    core_col = np.array([255.0, 245.0, 255.0], dtype=np.float32)

    t_mid = np.clip(dist / 10.0, 0.0, 1.0)[:, :, None]
    t_core = np.clip((dist - 10.0) / 14.0, 0.0, 1.0)[:, :, None]
    blade_col = edge_col * (1.0 - t_mid) + mid_col * t_mid
    blade_col = blade_col * (1.0 - t_core) + core_col * t_core

    new_diff = diff_arr * (1.0 - m3) + blade_col * m3
    new_diff = np.clip(new_diff, 0, 255).astype(np.uint8)

    # Unity / Blender emission preview texture (luminous white core + purple glow)
    unity_em = np.clip(blade_col * (em_mask[:, :, None] / 245.0), 0, 255).astype(np.uint8)

    print(
        f"[WPN_TEX] RoughMean={rough.mean():.1f}, AOMean={ao.mean():.1f}, "
        f"BladeMaskPixels={(mask_arr > 0.5).sum()}, BladeRAOE.B={em_mask[mask_arr > 0.5].mean():.1f}, "
        f"KabamNM.B={metallic.mean():.1f}"
    )

    files = {
        "cha_blitzwing_wpns_Diffuse.png": Image.fromarray(new_diff, "RGB"),
        "cha_blitzwing_wpns_Normal.png": Image.fromarray(norm_kabam, "RGB"),
        "cha_blitzwing_wpns_Normal_unity.png": Image.fromarray(norm_gl, "RGB"),
        "cha_blitzwing_wpns_RAOE.png": Image.fromarray(raoe_rgb, "RGB"),
        "cha_blitzwing_wpns_Emission.png": Image.fromarray(unity_em, "RGB"),
    }
    for d in (OUT_DIR, UNITY_TEX_DIR, STAGE_TEX_DIR):
        for fname, im in files.items():
            im.save(d / fname)
    print("[SAVED] cha_blitzwing_wpns_* textures to OUT_DIR, UNITY_TEX_DIR, STAGE_TEX_DIR.")


if __name__ == "__main__":
    build_weapon_textures()
