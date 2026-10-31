#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_clean_elita_textures.py

Rebuilds 100% clean, authoritative PBR textures for Galactic Trials Elita One directly
from the raw 2048x2048 source sheets and packs them into Kabam's exact 3-material
Arcee UV & PBR channel contract:

1. Kabam Normal + Metallic Packing (`_normal_tex` = `main_NM` & `tform_misc_NM`):
   - R = Tangent Normal Nx (preserved 1:1 from raw normal map)
   - G = Tangent Normal Ny (preserved 1:1 from raw normal map)
   - B = Per-pixel Metallic Mask! (In Kabam's Character/PBR `_METALLIC_TEX` shader,
         `NM.B` is Metallic, NOT Nz! Passing UE4's `Nz=254` made 100% of Elita's body
         bare chrome metal that mirrored dark yellow-brown stage cubemaps. We pack
         `NM.B = 0` pure dielectric ceramic/paint on all white armor, face, pink armor,
         tires, and lights, and subtle `95` satin gunmetal ONLY on bare dark grey joints.)
   - A = 255

2. Snow-Pearl White & Fresh Sakura/Rose-Pink Albedo Grading (`_base_tex`):
   - Smoothly lifts raw Galactic Trials taupe-grey "white" regions (`[194, 168, 167]` on
     Robot face/chest/arms/thighs, `[145, 145, 145]` on Vehicle pods) up to Arcee's
     crisp feminine snow-pearl white (`p50 ~ [241, 239, 241]`), preserving 100% of
     delicate lip/nose/cheek 3D sculpting, silver Autobot emblem line art, and panel seams.
   - Gently lifts under-exposed Robot pastel-pink & rose-pink armor to match Vehicle & Arcee
     vibrancy while keeping crimson Autobot insignias and dark charcoal joints crisp.

3. Satin Ceramic Roughness, Airy AO & Verified 3D Eye/Crest Emissive (`RAOE`):
   - R = Silky matte-satin Roughness (`142..218` on Robot, `>= 188` porcelain-satin on
         white armor & face so dark background shipping containers never mirror!)
   - G = Clean airy Ambient Occlusion (`190..255`)
   - B = Authoritative Emissive Mask (full `255` ice-cyan 3D eye lenses + golden visor crest,
         guaranteed `0` stray emissive on sculpted face/forehead skin).
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures"
OUT_DIR = ROOT / "tools" / "elita_one" / "processed_textures"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def grade_elita_pbr_sheet(d_rgb_u8, r_u8, is_vehicle=False):
    """
    Continuous, halo-free PBR albedo, Kabam metallic (for NM.B), and satin roughness
    grading tailored to Kabam's Character/PBR shader and Arcee's pearl-white benchmark.
    """
    rgb = d_rgb_u8.astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    chroma = max_c - min_c
    sat = chroma / np.maximum(max_c, 1.0)
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # Exclude cyan/blue/yellow/green indicator lights smoothly
    not_colored_light = (
        np.clip(1.0 - np.maximum(0.0, (b - r) - 5.0) / 14.0, 0.0, 1.0)
        * np.clip(1.0 - np.maximum(0.0, (g - r) - 5.0) / 14.0, 0.0, 1.0)
        * np.clip(1.0 - np.maximum(0.0, (g - b) - 20.0) / 18.0, 0.0, 1.0)
    )

    if not is_vehicle:
        # Smoothly capture all pale white/taupe regions (including warm-shaded temples up to sat~0.24)
        # across the natural empty saturation gap [0.23 .. 0.31] below Light Pastel Pink (sat~0.38+)
        w_sat = np.clip((0.31 - sat) / 0.08, 0.0, 1.0)
        w_lum = np.clip((lum - 106.0) / 28.0, 0.0, 1.0)
    else:
        # Vehicle silver-white side pods (lum >= 134, sat < 0.18) vs dark grey joints (lum <= 115)
        w_sat = np.clip((0.20 - sat) / 0.07, 0.0, 1.0)
        w_lum = np.clip((lum - 124.0) / 16.0, 0.0, 1.0)

    w_white = w_sat * w_lum * not_colored_light

    # Detail-preserving snow-pearl white curve:
    # - Robot lum=174 -> 240.0 crisp snow-pearl white (matches Arcee p50=[241, 241, 241])
    # - Sculpted shadows lum=140 -> 217.9 (preserves 3D lip/nose/cheek contour & panel lines)
    # - Already-bright silver Autobot crest (lum > 196) tapers gently so internal line art stays razor-sharp
    if not is_vehicle:
        delta = lum - 174.0
        base_lift = np.where(
            delta <= 0.0,
            240.0 + delta * 0.65,
            240.0 + 13.0 * np.tanh(delta / 26.0),
        )
        w_hi = np.clip((lum - 196.0) / 26.0, 0.0, 1.0)
        lifted_l = base_lift * (1.0 - w_hi) + np.clip(lum + 18.0, 0.0, 248.0) * w_hi
    else:
        delta = lum - 148.0
        lifted_l = np.where(
            delta <= 0.0,
            236.0 + delta * 0.70,
            236.0 + 16.0 * np.tanh(delta / 32.0),
        )
    lifted_l = np.clip(lifted_l, 145.0, 252.0)

    # Pure feminine snow-pearl white (95% neutral pearl + 5% subtle warmth)
    scale_ratio = lifted_l / np.maximum(lum, 1.0)
    pearl_r = lifted_l * 1.004
    pearl_g = lifted_l * 0.997
    pearl_b = lifted_l * 1.004
    white_target = np.stack([
        0.95 * pearl_r + 0.05 * np.clip(r * scale_ratio, 0.0, 254.0),
        0.95 * pearl_g + 0.05 * np.clip(g * scale_ratio, 0.0, 253.0),
        0.95 * pearl_b + 0.05 * np.clip(b * scale_ratio, 0.0, 254.0),
    ], axis=-1)

    # Lift under-exposed Robot pastel-pink & rose-pink armor to match Arcee & Vehicle vibrancy,
    # while protecting pure crimson Autobot insignias (g < 48 and b < 58)
    if not is_vehicle:
        is_crimson_badge = np.clip((48.0 - g) / 14.0, 0.0, 1.0) * np.clip((58.0 - b) / 14.0, 0.0, 1.0)
        w_pink = np.clip(((r - g) - 28.0) / 26.0, 0.0, 1.0) * (1.0 - w_white) * (1.0 - 0.85 * is_crimson_badge)
        pink_target = np.stack([
            np.clip(((r / 255.0) ** 0.65) * 255.0, 0.0, 252.0),
            np.clip(((g / 255.0) ** 0.78) * 255.0 + 8.0, 0.0, 246.0),
            np.clip(((b / 255.0) ** 0.75) * 255.0 + 12.0, 0.0, 248.0),
        ], axis=-1)
    else:
        w_pink = np.clip(((r - g) - 35.0) / 30.0, 0.0, 1.0) * (1.0 - w_white) * 0.30
        pink_target = np.stack([
            np.clip(r * 1.01, 0.0, 253.0),
            np.clip(g * 1.05 + 5.0, 0.0, 246.0),
            np.clip(b * 1.05 + 5.0, 0.0, 248.0),
        ], axis=-1)

    out = (
        rgb * (1.0 - w_white[:, :, None] - w_pink[:, :, None])
        + white_target * w_white[:, :, None]
        + pink_target * w_pink[:, :, None]
    )
    out_u8 = np.clip(out, 0.0, 255.0).astype(np.uint8)

    # Kabam Metallic mask (for Normal Map Blue channel `NM.B`):
    # 0 (pure dielectric) on ALL white armor, face, pink armor, tires, and glowing lights;
    # subtle 95 ONLY on bare dark neutral mechanical joints (lum in [44, 116], sat < 0.15)
    w_mech = (
        np.clip((0.15 - sat) / 0.05, 0.0, 1.0)
        * np.clip((lum - 44.0) / 14.0, 0.0, 1.0)
        * np.clip((116.0 - lum) / 16.0, 0.0, 1.0)
        * (1.0 - w_white)
    )
    metallic_u8 = np.clip(w_mech * 95.0, 0.0, 100.0).astype(np.uint8)

    # Silky Matte-Satin Ceramic Roughness (for `RAOE.R`):
    r_f = r_u8.astype(np.float32)
    if not is_vehicle:
        r_satin = np.clip(r_f * 1.05 + 18.0, 142.0, 218.0)
        r_satin = np.maximum(r_satin, w_white * 188.0)
    else:
        r_satin = np.clip(r_f * 0.85 + 12.0, 108.0, 168.0)
        r_satin = np.maximum(r_satin, w_white * 142.0)
    rough_u8 = np.clip(r_satin, 0.0, 255.0).astype(np.uint8)

    return out_u8, metallic_u8, rough_u8, w_white


def build_sheet(d_name, n_name, r_name, o_name, glow_name, is_ch00=False, is_vehicle=False):
    """
    Loads raw 2048x2048 Galactic Trials sheets, grades snow-pearl white & sakura-pink
    albedo, packs Kabam `(Nx, Ny, Metallic, 255)` normal maps, builds satin `RAOE`, and
    infuses emissive colors strictly inside official glow islands.
    Returns (diff_2048_rgba, kabam_norm_2048_rgba, unity_std_norm_2048_rgba, raoe_2048_rgb, glow_2048_rgb).
    """
    d_img = Image.open(RAW_DIR / d_name).convert("RGBA")
    n_img = Image.open(RAW_DIR / n_name).convert("RGBA")
    r_img = Image.open(RAW_DIR / r_name).convert("L")
    o_img = Image.open(RAW_DIR / o_name).convert("L")

    W, H = d_img.size
    d_raw_rgb = np.array(d_img, dtype=np.uint8)[:, :, :3]
    r_raw_u8 = np.array(r_img, dtype=np.uint8)

    # 1. Snow-pearl white + fresh sakura-pink albedo, Kabam metallic mask, and satin roughness
    d_rgb, metallic_u8, r_arr, w_white = grade_elita_pbr_sheet(d_raw_rgb, r_raw_u8, is_vehicle=is_vehicle)

    # 2. Official glow infusion (strictly inside glow mask islands)
    glow_path = RAW_DIR / glow_name
    if glow_path.is_file():
        g_img = Image.open(glow_path).convert("RGB")
        if g_img.size != (W, H):
            g_img = g_img.resize((W, H), Image.BILINEAR)
        g_rgb = np.array(g_img, dtype=np.uint8)
    else:
        g_rgb = np.zeros((H, W, 3), dtype=np.uint8)

    g_max = g_rgb.max(axis=-1)
    glow_mask = g_max > 38

    d_rgb[glow_mask] = np.maximum(d_rgb[glow_mask], g_rgb[glow_mask])
    metallic_u8[glow_mask] = 0  # Emissive lenses/strips are pure dielectric

    # 3. Airy lifted Ambient Occlusion (RAOE.G) & Emissive Mask (RAOE.B)
    ao_norm = np.array(o_img, dtype=np.float32) / 255.0
    ao_arr = np.clip(190.0 + (ao_norm ** 0.65) * 65.0, 190.0, 255.0).astype(np.uint8)

    e_arr = np.zeros((H, W), dtype=np.uint8)
    e_arr[glow_mask] = np.clip(g_max[glow_mask].astype(np.int32) + 25, 185, 255).astype(np.uint8)

    if is_ch00:
        # True 3D eye lens UV island in 2048x2048: X in [215, 280], Y in [790, 910]
        eye_box = np.zeros((H, W), dtype=bool)
        eye_box[790:910, 215:280] = True
        eye_mask = eye_box & (g_max > 30)
        ice_cyan = np.array([155, 232, 255], dtype=np.uint8)
        d_rgb[eye_mask] = np.maximum(d_rgb[eye_mask], ice_cyan)
        e_arr[eye_mask] = 255
        metallic_u8[eye_mask] = 0
        # Guarantee zero stray emissive on sculpted snow-pearl white face / forehead / collar (X<430, Y<380)
        e_arr[:380, :430] = 0
        print(f"  [CH11_00] True 3D eye lens lit pixels: {int(eye_mask.sum())}, Face stray emissive: {int(e_arr[:380, :430].max())}")

    # 4. Pack Kabam Normal + Metallic texture: R=Nx, G=Ny, B=Metallic, A=255
    n_raw = np.array(n_img, dtype=np.uint8)
    kabam_nm = np.dstack([
        n_raw[:, :, 0],
        n_raw[:, :, 1],
        metallic_u8,
        np.full((H, W), 255, dtype=np.uint8),
    ])

    w_mask = w_white > 0.65
    w_mean = d_rgb[w_mask].mean(axis=0).round(1) if w_mask.any() else [0, 0, 0]
    print(
        f"  [{d_name}] Pearl-White RGB mean={w_mean} | White NM.B(Metallic)={metallic_u8[w_mask].mean():.2f} "
        f"| White RAOE.R(Roughness)={r_arr[w_mask].mean():.1f}"
    )

    d_out = np.dstack([d_rgb, np.full((H, W), 255, dtype=np.uint8)])
    raoe_out = np.stack([r_arr, ao_arr, e_arr], axis=-1)

    return (
        Image.fromarray(d_out, "RGBA"),
        Image.fromarray(kabam_nm, "RGBA"),
        n_img,
        Image.fromarray(raoe_out, "RGB"),
        Image.fromarray(g_rgb, "RGB"),
    )


def main():
    print("=== Building Pearl-White & Dielectric Satin PBR Elita One Textures ===")
    ch00_d, ch00_nm_kabam, ch00_n_std, ch00_raoe, ch00_glow = build_sheet(
        "T_CH11_00_D.png", "T_CH11_00_N.png", "T_CH11_00_R.png", "T_CH11_00_O.png", "MI_CH11_00_glow.tga.png",
        is_ch00=True, is_vehicle=False
    )
    ch01_d, ch01_nm_kabam, ch01_n_std, ch01_raoe, _ = build_sheet(
        "T_CH11_01_D.png", "T_CH11_01_N.png", "T_CH11_01_R.png", "T_CH11_01_O.png", "MI_CH11_01_glow.tga.png",
        is_ch00=False, is_vehicle=False
    )
    vh00_d, vh00_nm_kabam, _, vh00_raoe, _ = build_sheet(
        "T_VH11_00_D.png", "T_VH11_00_N.png", "T_VH11_00_R.png", "T_VH11_00_O.png", "mat_vh0_glow.tga.png",
        is_ch00=False, is_vehicle=True
    )
    vh01_d, vh01_nm_kabam, _, vh01_raoe, _ = build_sheet(
        "T_VH11_01_D.png", "T_VH11_01_N.png", "T_VH11_01_R.png", "T_VH11_01_O.png", "mat_vh1_glow.tga.png",
        is_ch00=False, is_vehicle=True
    )

    # 1. Robot Submesh[0] main textures (1024x1024)
    main_diff_1024 = ch00_d.resize((1024, 1024), Image.LANCZOS)
    main_norm_kabam_1024 = ch00_nm_kabam.resize((1024, 1024), Image.LANCZOS)
    main_norm_std_1024 = ch00_n_std.resize((1024, 1024), Image.LANCZOS)
    main_raoe_1024 = ch00_raoe.resize((1024, 1024), Image.NEAREST)
    main_glow_1024 = ch00_glow.resize((1024, 1024), Image.BILINEAR)

    main_diff_1024.save(OUT_DIR / "elita_main_diffuse.png")
    main_norm_kabam_1024.save(OUT_DIR / "elita_main_normal.png")
    main_raoe_1024.save(OUT_DIR / "elita_main_raoe.png")
    print("[✓] Saved Pearl-White & Kabam (Nx,Ny,Metallic) elita_main_diffuse/normal/raoe (1024x1024)")

    # 2. Combined tform_misc_A (2048x2048):
    #    Top Half (Y: 0..1024)       = [1024x1024 VH00_D | 1024x1024 VH01_D]  (Vehicle Mode)
    #    Bottom Half (Y: 1024..2048) = 2048x1024 CH11_01_D                    (Robot Submesh[1])
    tform_diff = Image.new("RGBA", (2048, 2048))
    tform_diff.paste(vh00_d.resize((1024, 1024), Image.LANCZOS), (0, 0))
    tform_diff.paste(vh01_d.resize((1024, 1024), Image.LANCZOS), (1024, 0))
    tform_diff.paste(ch01_d.resize((2048, 1024), Image.LANCZOS), (0, 1024))
    tform_diff.save(OUT_DIR / "elita_tform_misc_diffuse.png")
    tform_diff.save(OUT_DIR / "elita_veh_atlas_diffuse.png")
    print("[✓] Saved unified Pearl-White elita_tform_misc_diffuse.png (2048x2048: Top=[VH00|VH01], Bottom=CH11_01)")

    # 3. Combined Kabam tform_misc_NM (1024x1024, with Blue = Metallic mask!):
    #    Top Half (Y: 0..512)      = [512x512 VH00_NM | 512x512 VH01_NM]
    #    Bottom Half (Y: 512..1024)= 1024x512 CH11_01_NM
    tform_norm = Image.new("RGBA", (1024, 1024))
    tform_norm.paste(vh00_nm_kabam.resize((512, 512), Image.LANCZOS), (0, 0))
    tform_norm.paste(vh01_nm_kabam.resize((512, 512), Image.LANCZOS), (512, 0))
    tform_norm.paste(ch01_nm_kabam.resize((1024, 512), Image.LANCZOS), (0, 512))
    tform_norm.save(OUT_DIR / "elita_tform_misc_normal.png")
    tform_norm.save(OUT_DIR / "elita_veh_atlas_normal.png")
    print("[✓] Saved unified Kabam (Nx,Ny,Metallic) elita_tform_misc_normal.png (1024x1024)")

    # 4. Combined main_tform_misc_RAOE (1024x2048):
    #    Top Half (X: 0..1024, Y: 0..1024)          = 1024x1024 CH11_00_RAOE
    #    Bottom-Left (X: 0..512, Y: 1024..2048)     = 512x1024  CH11_01_RAOE
    #    Bottom-Right (X: 512..1024, Y: 1024..2048) = [256x1024 VH00_RAOE | 256x1024 VH01_RAOE]
    comb_raoe = Image.new("RGB", (1024, 2048))
    comb_raoe.paste(main_raoe_1024, (0, 0))
    comb_raoe.paste(ch01_raoe.resize((512, 1024), Image.NEAREST), (0, 1024))
    comb_raoe.paste(vh00_raoe.resize((256, 1024), Image.NEAREST), (512, 1024))
    comb_raoe.paste(vh01_raoe.resize((256, 1024), Image.NEAREST), (768, 1024))
    comb_raoe.save(OUT_DIR / "elita_main_tform_misc_raoe.png")
    print("[✓] Saved unified Satin-Roughness elita_main_tform_misc_raoe.png (1024x2048)")

    # 5. Sync single-sheet preview textures into Unity project Assets/ElitaOne/
    #    (Use standard 3-axis (Nx, Ny, Nz) normal maps for Unity Editor's Standard shader!)
    if UNITY_DIR.is_dir():
        main_diff_1024.save(UNITY_DIR / "cha_elita_one_main_a.png")
        main_norm_std_1024.save(UNITY_DIR / "cha_elita_one_main_NM.png")
        main_raoe_1024.save(UNITY_DIR / "cha_elita_one_main_RAOE.png")
        main_glow_1024.save(UNITY_DIR / "cha_elita_one_main_Emission.png")
        ch01_d.resize((1024, 1024), Image.LANCZOS).save(UNITY_DIR / "cha_elita_one_vh_a.png")
        ch01_n_std.resize((1024, 1024), Image.LANCZOS).save(UNITY_DIR / "cha_elita_one_vh_NM.png")
        comb_raoe.save(UNITY_DIR / "cha_elita_one_main_tform_misc_RAOE.png")
        print("[✓] Synced Pearl-White preview textures to Unity Assets/ElitaOne/")


if __name__ == "__main__":
    main()
