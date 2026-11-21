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

    # Silver clearcoat armor (lum >= 65) vs dark chassis joints (lum < 65)
    is_silver_armor = (lum >= 65.0) & (sat < 0.25)
    is_dark_joint = (lum < 65.0)

    # Kabam metallic in NM.B: silver armor ~105, dark joints ~135
    metallic = np.where(is_silver_armor, 105.0, 50.0)
    metallic = np.where(is_dark_joint, 135.0, metallic)
    metallic = np.where(em_mask >= 30, 0.0, metallic)

    # Roughness (R): smooth silver lacquer ~175, gunmetal joints ~155
    rough = np.where(is_silver_armor, 178.0, 190.0)
    rough = np.where(is_dark_joint, 155.0, rough)

    # Soft cavity AO (G)
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

    em_factor = (em_mask.astype(np.float32) / 255.0)[..., None]
    unity_em = np.clip(df * em_factor * 1.5, 0, 255).astype(np.uint8)
    return nm_kabam, raoe, unity_em


def build_robot_atlas():
    print("\n--- Building Robot Atlas (cha_sideswipe_main, 2048x2048) ---")
    size = (2048, 2048)
    diff = load_rgb("Body_Diffuse.png", size)
    norm = load_normal_gl("Body_Normal.png", size)

    # Build clean emissive mask around eye optics
    # Eye position in 2048 space: Y in [1746, 1754], X in [742, 834]
    em_mask = np.zeros(size, dtype=np.uint8)
    
    # Fill eye visor area with gradient glow
    for y in range(1738, 1762):
        for x in range(736, 840):
            # calculate distance to center
            cy = 1750.0
            cx = 788.0
            dy = abs(y - cy) / 12.0
            dx = abs(x - cx) / 52.0
            dist = max(dx, dy)
            if dist <= 1.0:
                val = int(255.0 * (1.0 - dist * 0.4))
                em_mask[y, x] = max(em_mask[y, x], val)

    # Add chest accent light trapezoids (the iconic red chest vents from Image 2!)
    # On Sideswipe's chest: Y around 880..930, X around 580..680 and 880..980
    # Let's paint the two crisp angled chest light strips
    for y in range(890, 915):
        # Left chest vent
        for x in range(600, 680):
            if (x - 600) + (y - 890) * 0.5 < 70:
                em_mask[y, x] = 230
        # Right chest vent
        for x in range(880, 960):
            if (960 - x) + (y - 890) * 0.5 < 70:
                em_mask[y, x] = 230

    # Smooth the edges slightly
    em_img = Image.fromarray(em_mask).filter(ImageFilter.GaussianBlur(1.0))
    em_mask = np.array(em_img, dtype=np.uint8)

    # Boost diffuse in eye visor (cyan glow) and chest vents (crimson glow)
    df = diff.astype(np.float32)
    m = (em_mask.astype(np.float32) / 255.0)[..., None]
    
    # Eye region gets electric cyan
    eye_region = np.zeros((2048, 2048, 1), dtype=np.float32)
    eye_region[1730:1770, 720:860] = 1.0
    cyan_glow = np.array([45.0, 205.0, 255.0], dtype=np.float32)
    
    # Chest region gets crimson red (as seen in Image 2!)
    chest_region = np.zeros((2048, 2048, 1), dtype=np.float32)
    chest_region[870:940, :] = 1.0
    red_glow = np.array([255.0, 45.0, 35.0], dtype=np.float32)

    glow_target = cyan_glow * eye_region + red_glow * chest_region
    active_m = m * np.clip(eye_region + chest_region, 0, 1)
    diff = np.clip(df * (1.0 - active_m) + glow_target * active_m, 0, 255).astype(np.uint8)

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
