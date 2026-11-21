import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

SRC_TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures")
UNITY_TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Sideswipe\Textures")


def find_tex(name: str):
    p = SRC_TEX_DIR / name
    if p.exists():
        return p
    low = name.lower()
    for f in SRC_TEX_DIR.iterdir():
        if f.name.lower() == low:
            return f
    return None


def load_rgb(name: str, size, default_rgb=(180, 185, 190)) -> np.ndarray:
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
    fp = find_tex(name)
    if not fp:
        arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        arr[:, :] = (128, 128, 255)
        return arr
    im = Image.open(fp).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.uint8)
    # Flip G channel (DirectX -> OpenGL)
    arr[:, :, 1] = 255 - arr[:, :, 1]
    return arr


def compute_kabam_pbr_channels(diff_arr: np.ndarray, norm_gl: np.ndarray, em_mask: np.ndarray):
    df = diff_arr.astype(np.float32)
    lum = df.mean(axis=2)
    dmax = df.max(axis=2)
    dmin = df.min(axis=2)
    sat = (dmax - dmin) / np.maximum(dmax, 1.0)

    # Silver clearcoat armor (lum >= 40) vs dark chassis joints (lum < 40)
    is_silver_armor = (lum >= 40.0) & (sat < 0.22) & (em_mask < 30)
    is_dark_joint = (lum < 40.0) & (em_mask < 30)

    # Kabam metallic in NM.B: silver armor ~75 (brilliant clearcoat lacquer reflection), dark joints ~135 (gunmetal)
    metallic = np.where(is_silver_armor, 75.0, 50.0)
    metallic = np.where(is_dark_joint, 135.0, metallic)
    metallic = np.where(em_mask >= 30, 0.0, metallic)

    # Roughness (R): smooth silver lacquer ~105 (sharp specular sheen), gunmetal joints ~160, lights ~90
    rough = np.where(is_silver_armor, 105.0, 185.0)
    rough = np.where(is_dark_joint, 160.0, rough)
    rough = np.where(em_mask >= 30, 90.0, rough)

    # Soft cavity AO (G)
    ao = np.clip(215.0 + (lum / 255.0) * 40.0, 215.0, 255.0)

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


def build_robot_atlas():
    print("\n--- Building Robot Atlas (cha_sideswipe_main, 2048x2048) ---")
    size = (2048, 2048)
    diff = load_rgb("Body_Diffuse.png", size)
    norm = load_normal_gl("Body_Normal.png", size)

    # 1. Boost silver armor luminance to gleaming movie silver (mean ~170, max ~245)
    df = diff.astype(np.float32)
    lum = df.mean(axis=2)
    sat = (df.max(axis=2) - df.min(axis=2)) / np.maximum(df.max(axis=2), 1.0)
    is_silver = (lum >= 40.0) & (sat < 0.22)
    boost_factor = np.where(is_silver, np.clip(2.05 + (lum - 40.0) / 100.0 * 0.4, 1.8, 2.6), 1.0)[..., None]
    diff = np.clip(df * boost_factor, 0, 245).astype(np.uint8)

    # 2. Build precise emissive mask
    em_mask = np.zeros(size, dtype=np.uint8)

    # Eye optics: strictly only the two eye pupil centers from Body_Emission.png
    # Left eye optic (pinpoint cluster):
    em_mask[1748:1753, 744:748] = 200
    diff[1748:1753, 744:748] = [30, 165, 255]  # Electric Autobot Blue

    # Right eye optic (pinpoint cluster):
    em_mask[1748:1753, 828:832] = 200
    diff[1748:1753, 828:832] = [30, 165, 255]  # Electric Autobot Blue

    # Chest headlight patch in bottom-left corner of atlas:
    # Dedicated isolated region (PIL y in [2000..2048], x in [0..48], Blender UV u,v in [0..0.024])
    em_mask[2000:2048, 0:48] = 225
    diff[2000:2048, 0:48] = [255, 30, 20]  # Vibrant Crimson Red

    # 3. Fill chest taillight/headlight cavity on diffuse atlas with vibrant crimson red
    # (replaces the black shadow cavity so the pocket never renders as pitch black!)
    sub = diff[700:840, 785:875]
    sub_lum = sub.mean(axis=2)
    is_cavity = (sub_lum < 65) | ((sub[:, :, 0] > sub[:, :, 1] + 25) & (sub[:, :, 0] > sub[:, :, 2] + 25))
    is_silver = (sub_lum > 85) & (abs(sub[:, :, 0].astype(int) - sub[:, :, 1].astype(int)) < 25)
    is_cavity = is_cavity & (~is_silver)
    sub[is_cavity] = [235, 25, 20]  # Vibrant Crimson Red diffuse in pocket cavity

    em_pct = (em_mask > 20).mean() * 100.0
    print(f"  Robot Final Emissive Pixel Ratio: {em_pct:.3f}% (Target: 0.05%..20.0%)")

    nm_kabam, raoe_rgb, unity_em = compute_kabam_pbr_channels(diff, norm, em_mask)
    save_atlas_outputs("cha_sideswipe_main", diff, nm_kabam, norm, raoe_rgb, unity_em)


def build_vehicle_atlas():
    print("\n--- Building Vehicle Atlas (cha_sideswipe_tform_misc, 2048x2048) ---")
    diff_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)
    em_mask_atlas = np.zeros((2048, 2048), dtype=np.uint8)

    # Q0: Car Body (1024x1024)
    d_car = load_rgb("Car_Diffuse.png", (1024, 1024))
    n_car = load_normal_gl("Car_Normal.png", (1024, 1024))
    diff_atlas[0:1024, 0:1024] = d_car
    norm_unity_atlas[0:1024, 0:1024] = n_car

    # Headlights & Taillights in Car Body (targeted bounds):
    # Front headlights: Y in [60..140], X in [180..320] and [700..840]
    car_em = np.zeros((1024, 1024), dtype=np.uint8)
    car_df = d_car.astype(np.float32)
    
    # Headlight xenon bulbs (bright reflection in headlight cluster)
    head_cluster = np.zeros((1024, 1024), dtype=bool)
    head_cluster[50:180, 180:350] = True
    head_cluster[50:180, 680:850] = True
    is_head_bulb = head_cluster & (car_df.mean(axis=2) > 185)
    car_em[is_head_bulb] = 240

    # Taillights (rear bumper area): Y in [820..940], X in [200..380] and [640..820]
    tail_cluster = np.zeros((1024, 1024), dtype=bool)
    tail_cluster[800:960, 180:400] = True
    tail_cluster[800:960, 620:840] = True
    is_tail_bulb = tail_cluster & (car_df[:, :, 0] > 90) & (car_df[:, :, 1] < 70)
    car_em[is_tail_bulb] = 255

    # Dilate light mask slightly for realistic glow
    car_em = np.array(Image.fromarray(car_em).filter(ImageFilter.MaxFilter(3)), dtype=np.uint8)
    em_mask_atlas[0:1024, 0:1024] = car_em

    # Q1: Car Interior (1024x1024)
    d_int = load_rgb("CarInt_Diffuse.png", (1024, 1024))
    n_int = load_normal_gl("CarInt_Normal.png", (1024, 1024))
    diff_atlas[0:1024, 1024:2048] = d_int
    norm_unity_atlas[0:1024, 1024:2048] = n_int

    # Q2: Wheels (1024x1024)
    d_wheel = load_rgb("Wheel_Diffuse.png", (1024, 1024))
    n_wheel = load_normal_gl("Wheel_Normal.png", (1024, 1024))
    diff_atlas[1024:2048, 0:1024] = d_wheel
    norm_unity_atlas[1024:2048, 0:1024] = n_wheel

    # Q3: Autobot Crest Plate (1024x1024)
    d_plate = np.zeros((1024, 1024, 3), dtype=np.uint8)
    d_plate[:, :] = (38, 42, 45)  # Dark titanium chassis plate
    n_plate = np.zeros((1024, 1024, 3), dtype=np.uint8)
    n_plate[:, :] = (128, 128, 255)

    logo_fp = Path(r"P:\TFonics-V2\autobot.png")
    if logo_fp.exists():
        logo_im = Image.open(logo_fp).convert("RGBA").resize((600, 600), Image.Resampling.LANCZOS)
        la = np.array(logo_im, dtype=np.float32)
        alpha = la[:, :, 3:4] / 255.0
        crest_rgb = np.array([220.0, 35.0, 35.0], dtype=np.float32)
        d_plate[212:812, 212:812] = np.clip(
            d_plate[212:812, 212:812].astype(np.float32) * (1.0 - alpha) + crest_rgb * alpha,
            0, 255
        ).astype(np.uint8)
        # Subtle crest emissive
        em_plate = np.zeros((1024, 1024), dtype=np.uint8)
        em_plate[212:812, 212:812] = (alpha[:, :, 0] * 110).astype(np.uint8)
        em_mask_atlas[1024:2048, 1024:2048] = em_plate

    diff_atlas[1024:2048, 1024:2048] = d_plate
    norm_unity_atlas[1024:2048, 1024:2048] = n_plate

    veh_em_pct = (em_mask_atlas > 20).mean() * 100.0
    print(f"  Vehicle Final Emissive Pixel Ratio: {veh_em_pct:.3f}% (Target: 0.05%..20.0%)")

    nm_kabam, raoe_rgb, unity_em = compute_kabam_pbr_channels(diff_atlas, norm_unity_atlas, em_mask_atlas)
    save_atlas_outputs("cha_sideswipe_tform_misc", diff_atlas, nm_kabam, norm_unity_atlas, raoe_rgb, unity_em)


def save_atlas_outputs(prefix, diff, nm_kabam, norm_unity, raoe_rgb, unity_em):
    em_pct = (raoe_rgb[:, :, 2] > 20).mean() * 100.0
    r_mean = raoe_rgb[:, :, 0].mean()
    nm_b_mean = nm_kabam[:, :, 2].mean()
    nu_b_mean = norm_unity[:, :, 2].mean()
    print(f"  [{prefix}] RAOE mode=RGB, RoughMean={r_mean:.1f}, EmissivePct={em_pct:.2f}%, NM.B Mean={nm_b_mean:.1f}, NM_unity.B Mean={nu_b_mean:.1f}")

    outputs = {
        f"{prefix}_Diffuse.png": Image.fromarray(diff, "RGB"),
        f"{prefix}_Normal.png": Image.fromarray(nm_kabam, "RGB"),
        f"{prefix}_Normal_unity.png": Image.fromarray(norm_unity, "RGB"),
        f"{prefix}_RAOE.png": Image.fromarray(raoe_rgb, "RGB"),
        f"{prefix}_Emission.png": Image.fromarray(unity_em, "RGB"),
    }
    for d in (OUT_DIR, UNITY_TEX_DIR):
        for fname, im in outputs.items():
            out_p = d / fname
            im.save(out_p)
            print(f"    Saved: {out_p}")


if __name__ == "__main__":
    print("=== [Sideswipe] Building Production 2048x2048 PBR Texture Atlases ===")
    build_robot_atlas()
    build_vehicle_atlas()
    print("\n[✓] All Sideswipe PBR textures built cleanly!")
