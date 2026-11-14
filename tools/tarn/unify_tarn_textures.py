import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
BAKED_DIR = TARN_ROOT / "06_working" / "robot_baked_raw"
VEH_PREP_DIR = TARN_ROOT / "03_vehicle_preprocessed_tftf"
OUT_DIR = TARN_ROOT / "06_working" / "unified_textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def unify_robot_textures():
    palette = json.loads((VEH_PREP_DIR / "tarn_palette_target.json").read_text(encoding="utf-8"))["regions"]

    req = [
        "tarn_robot_albedo.png",
        "tarn_robot_normal_std.png",
        "tarn_robot_roughness.png",
        "tarn_robot_ao.png",
        "tarn_robot_emission.png",
        "tarn_robot_metallic.png",
    ]
    for fn in req:
        if not (BAKED_DIR / fn).is_file():
            raise FileNotFoundError(f"Missing baked file: {BAKED_DIR / fn}")

    alb = np.array(Image.open(BAKED_DIR / "tarn_robot_albedo.png").convert("RGB"), dtype=np.float32)
    nrm = np.array(Image.open(BAKED_DIR / "tarn_robot_normal_std.png").convert("RGB"))
    ao = np.array(Image.open(BAKED_DIR / "tarn_robot_ao.png").convert("L"), dtype=np.float32)
    emit_rgb = np.array(Image.open(BAKED_DIR / "tarn_robot_emission.png").convert("RGB"), dtype=np.float32)
    metal_raw = np.array(Image.open(BAKED_DIR / "tarn_robot_metallic.png").convert("L"), dtype=np.float32)
    rough_raw = np.array(Image.open(BAKED_DIR / "tarn_robot_roughness.png").convert("L"), dtype=np.float32)
    H, W, _ = alb.shape

    r, g, b = alb[:, :, 0], alb[:, :, 1], alb[:, :, 2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    sat = (max_c - min_c) / np.maximum(max_c, 1.0)

    # 1. Separate Emissive into Crimson-Red Eyes, Warm Gold Radiator Vents, and Neon-Magenta Energy
    emit_lum = emit_rgb.max(axis=-1)
    er, eg, eb = emit_rgb[:, :, 0], emit_rgb[:, :, 1], emit_rgb[:, :, 2]
    is_emit = emit_lum > 24.0
    is_eye_red = is_emit & (er > eb * 1.75) & (er > eg * 1.65)
    is_vent_gold = is_emit & (~is_eye_red) & (er > eb * 1.55)
    is_warm_emit = is_eye_red | is_vent_gold
    is_magenta_glow = is_emit & (~is_warm_emit)

    glow_mask_raw = Image.fromarray(np.where(is_emit, 255, 0).astype(np.uint8), "L")
    glow_feathered = np.maximum(
        np.array(glow_mask_raw, dtype=np.float32),
        np.array(glow_mask_raw.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32),
    )
    w_glow = np.clip(glow_feathered / 255.0, 0.0, 1.0)

    warm_mask_raw = Image.fromarray(np.where(is_warm_emit, 255, 0).astype(np.uint8), "L")
    warm_feathered = np.maximum(
        np.array(warm_mask_raw, dtype=np.float32),
        np.array(warm_mask_raw.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32),
    )
    w_warm = np.clip(warm_feathered / 255.0, 0.0, 1.0)

    red_mask_raw = Image.fromarray(np.where(is_eye_red, 255, 0).astype(np.uint8), "L")
    red_feathered = np.maximum(
        np.array(red_mask_raw, dtype=np.float32),
        np.array(red_mask_raw.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32),
    )
    w_eye = np.clip(red_feathered / 255.0, 0.0, 1.0)
    w_vent = np.clip(w_warm - w_eye, 0.0, 1.0)
    w_mag = np.clip(w_glow - w_warm, 0.0, 1.0)

    # 2. Continuous material partition weights
    w_purple = np.clip((b - g) / 22.0, 0.0, 1.0) * np.clip((sat - 0.18) / 0.14, 0.0, 1.0) * (1.0 - w_glow)
    w_gold = np.clip((r - b - 24.0) / 24.0, 0.0, 1.0) * np.clip((g - b - 8.0) / 18.0, 0.0, 1.0) * (1.0 - w_glow)
    w_silver = np.clip((0.26 - sat) / 0.10, 0.0, 1.0) * np.clip((lum - 85.0) / 28.0, 0.0, 1.0) * (1.0 - w_glow)
    w_dark = np.clip(1.0 - w_glow - w_purple - w_gold - w_silver, 0.0, 1.0)

    # 3. Color grade to Tarn calibrated palette (matched to Tarn_Vehicle)
    p_tgt = np.array(palette["purple_armor"]["median_rgb"], dtype=np.float32)
    if (w_purple > 0.6).any():
        p_cur = np.median(alb[w_purple > 0.6], axis=0)
        p_scale = np.clip(p_tgt / np.maximum(p_cur, 8.0), 0.55, 1.75)
    else:
        p_scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    purple_graded = np.clip(alb * p_scale[None, None, :], 0, 255)

    dark_graded = np.stack(
        [
            np.clip(17.0 + r * 0.65, 14, 70),
            np.clip(16.0 + g * 0.65, 14, 70),
            np.clip(22.0 + b * 0.65, 18, 82),
        ],
        axis=-1,
    )

    mag_tgt = np.array(palette["neon_magenta_emissive"]["base_rgb"], dtype=np.float32)
    eye_tgt = np.array([255.0, 24.0, 38.0], dtype=np.float32)
    vent_tgt = np.array([255.0, 165.0, 24.0], dtype=np.float32)

    glow_den = np.maximum(w_eye + w_vent + w_mag, 1e-4)[:, :, None]
    glow_color = (
        eye_tgt[None, None, :] * w_eye[:, :, None]
        + vent_tgt[None, None, :] * w_vent[:, :, None]
        + mag_tgt[None, None, :] * w_mag[:, :, None]
    ) / glow_den

    alb_unified = (
        purple_graded * w_purple[:, :, None]
        + dark_graded * w_dark[:, :, None]
        + alb * (w_silver[:, :, None] + w_gold[:, :, None])
        + glow_color * w_glow[:, :, None]
    )

    ao_mult = 0.58 + 0.42 * (ao[:, :, None] / 255.0)
    alb_unified = np.clip(alb_unified * ao_mult, 0, 255)
    alb_unified = np.where(w_glow[:, :, None] > 0.35, glow_color, alb_unified)
    Image.fromarray(np.dstack([alb_unified.astype(np.uint8), np.full((H, W), 255, dtype=np.uint8)]), "RGBA").save(
        OUT_DIR / "cha_tarn_main_a.png"
    )

    # Save dedicated RGB Emission map for Unity / shader preview
    emit_out = np.clip(glow_color * w_glow[:, :, None], 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([emit_out, np.full((H, W), 255, dtype=np.uint8)]), "RGBA").save(
        OUT_DIR / "cha_tarn_main_Emission.png"
    )

    # 4. Kabam NM_kabam (B = Metallic: purple=0, glow=0, dark=18..40, silver=110..165, gold=155)
    metal_b = (
        w_purple * 0.0
        + w_glow * 0.0
        + w_dark * np.clip(metal_raw * 0.25, 18.0, 40.0)
        + w_silver * np.clip(metal_raw * 0.65 + 45.0, 110.0, 165.0)
        + w_gold * 155.0
    )
    metal_u8 = np.clip(metal_b, 0, 255).astype(np.uint8)
    Image.fromarray(
        np.stack([nrm[:, :, 0], nrm[:, :, 1], metal_u8, np.full((H, W), 255, dtype=np.uint8)], axis=-1),
        "RGBA",
    ).save(OUT_DIR / "cha_tarn_main_NM_kabam.png")
    Image.fromarray(
        np.stack([nrm[:, :, 0], nrm[:, :, 1], nrm[:, :, 2], np.full((H, W), 255, dtype=np.uint8)], axis=-1),
        "RGBA",
    ).save(OUT_DIR / "cha_tarn_main_NM_std.png")

    # 5. RAOE (R=Roughness, G=AO >= 165, B=A=Emissive mask 0..255 with 0 on all non-glow)
    rough_r = (
        w_purple * np.clip(182.0 + (rough_raw / 255.0) * 28.0, 180, 214)
        + w_silver * np.clip(145.0 + (rough_raw / 255.0) * 25.0, 142, 175)
        + w_gold * 156.0
        + w_dark * np.clip(218.0 + (rough_raw / 255.0) * 22.0, 215, 242)
        + w_glow * 165.0
    ).astype(np.uint8)
    ao_airy = np.clip(165.0 + ((ao / 255.0) ** 0.72) * 90.0, 165, 255).astype(np.uint8)
    em_u8 = np.clip(glow_feathered, 0, 255).astype(np.uint8)
    Image.fromarray(np.stack([rough_r, ao_airy, em_u8, em_u8], axis=-1), "RGBA").save(
        OUT_DIR / "cha_tarn_main_RAOE.png"
    )

    print(
        f"[✓] Unified robot textures ({W}x{H}): dielectric={(metal_u8 < 20).mean()*100:.1f}%, "
        f"glow_px={(em_u8 > 200).mean()*100:.2f}%, eye_px={(is_eye_red).sum()}, "
        f"vent_px={(is_vent_gold).sum()}, mag_px={(is_magenta_glow).sum()}"
    )


def sync_vehicle_textures():
    mapping = {
        "tarn_veh_base_graded.png": "cha_tarn_tform_misc_A.png",
        "tarn_veh_normal_kabam.png": "cha_tarn_tform_misc_NM_kabam.png",
        "tarn_veh_normal_std.png": "cha_tarn_tform_misc_NM_std.png",
        "tarn_veh_raoe.png": "cha_tarn_tform_misc_RAOE.png",
    }
    for src, dst in mapping.items():
        sp = VEH_PREP_DIR / src
        if sp.is_file():
            shutil.copy2(sp, OUT_DIR / dst)
    # Also create vehicle RGB Emission map from A & mask
    veh_base = np.array(Image.open(VEH_PREP_DIR / "tarn_veh_base_graded.png").convert("RGB"), dtype=np.float32)
    veh_mask = np.array(Image.open(VEH_PREP_DIR / "tarn_veh_emissive_mask.png").convert("L"), dtype=np.float32) / 255.0
    veh_emit = np.clip(veh_base * veh_mask[:, :, None], 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([veh_emit, np.full(veh_mask.shape, 255, dtype=np.uint8)]), "RGBA").save(
        OUT_DIR / "cha_tarn_tform_misc_Emission.png"
    )
    print("[✓] Synced vehicle textures to 06_working/unified_textures/")


if __name__ == "__main__":
    sync_vehicle_textures()
    unify_robot_textures()
