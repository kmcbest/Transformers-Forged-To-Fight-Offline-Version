#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_clean_elita_textures.py

Rebuilds 100% clean, authoritative textures for Galactic Trials Elita One directly
from the raw 2048x2048 source sheets without any fake painted face/collar blobs,
and packs them into Kabam's exact 3-material Arcee UV atlas contract:

1. Robot Submesh[0] (Mat -737396187749761411, CH11_00: Head, 3D Eye Lenses, Crest, Chest, Arms):
   - cha_arcee_gs_deluxe2014_main_a : scale=(1.0, 1.0), offset=(0.0, 0.0) -> elita_main_diffuse.png (1024x1024)
   - main_NM                        : scale=(1.0, 1.0), offset=(0.0, 0.0) -> elita_main_normal.png  (1024x1024)
   - main_tform_misc_RAOE           : scale=(1.0, 0.5), offset=(0.0, 0.5) -> Top 1024x1024 of elita_main_tform_misc_raoe.png (1024x2048)

2. Robot Submesh[1] (Mat 5182645448333425879, CH11_01: Lower Torso, Legs, Wheels):
   - tform_misc_A                   : scale=(1.0, 0.5), offset=(0.0, 0.0) -> Bottom 2048x1024 of elita_tform_misc_diffuse.png (2048x2048)
   - tform_misc_NM                  : scale=(1.0, 0.5), offset=(0.0, 0.0) -> Bottom 1024x512  of elita_tform_misc_normal.png  (1024x1024)
   - main_tform_misc_RAOE           : scale=(0.5, 0.5), offset=(0.0, 0.0) -> Bottom-Left 512x1024 of elita_main_tform_misc_raoe.png

3. Vehicle Mode (Mat 6920099848281342549, Horizontal [VH11_00 | VH11_01] + Tinted Cockpit Glass):
   - tform_misc_A                   : scale=(1.0, 0.5), offset=(0.0, 0.5) -> Top 2048x1024 [1024x1024 VH00 | 1024x1024 VH01]
   - tform_misc_NM                  : scale=(1.0, 0.5), offset=(0.0, 0.5) -> Top 1024x512  [512x512  VH00 | 512x512  VH01]
   - main_tform_misc_RAOE           : scale=(0.5, 0.5), offset=(0.5, 0.0) -> Bottom-Right 512x1024 [256x1024 VH00 | 256x1024 VH01]
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


def build_sheet(d_name, n_name, r_name, o_name, glow_name, is_ch00=False):
    """
    Loads raw 2048x2048 Galactic Trials sheets, applies emissive color infusion strictly
    within the official glow islands (so Kabam's `_base_tex.rgb * RAOE.b` shader blooms
    with true ice-cyan eyes and golden crest while keeping face/armor 100% clean),
    and returns (diff_2048_rgba, norm_2048_rgba, raoe_2048_rgb, glow_2048_rgb).
    """
    d_img = Image.open(RAW_DIR / d_name).convert("RGBA")
    n_img = Image.open(RAW_DIR / n_name).convert("RGBA")
    r_img = Image.open(RAW_DIR / r_name).convert("L")
    o_img = Image.open(RAW_DIR / o_name).convert("L")

    W, H = d_img.size
    d_arr = np.array(d_img, dtype=np.uint8)
    d_rgb = d_arr[:, :, :3].copy()

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

    # Infuse glow color into diffuse strictly inside official glow islands
    d_rgb[glow_mask] = np.maximum(d_rgb[glow_mask], g_rgb[glow_mask])

    # Build RAOE (R = Roughness, G = AO, B = Emissive mask)
    r_arr = np.clip(np.array(r_img, dtype=np.float32) * 0.35, 20.0, 110.0).astype(np.uint8)
    ao_norm = np.array(o_img, dtype=np.float32) / 255.0
    ao_arr = np.clip(165.0 + (ao_norm ** 0.7) * 90.0, 165.0, 255.0).astype(np.uint8)

    e_arr = np.zeros((H, W), dtype=np.uint8)
    e_arr[glow_mask] = np.clip(g_max[glow_mask].astype(np.int32) + 25, 185, 255).astype(np.uint8)

    if is_ch00:
        # True 3D eye lens UV island in 2048x2048: X in [215, 280], Y in [790, 910]
        eye_box = np.zeros((H, W), dtype=bool)
        eye_box[790:910, 215:280] = True
        eye_mask = eye_box & (g_max > 30)
        # Crisp radiant Cybertronian ice-cyan on the 3D eye lenses + full 255 emissive mask
        ice_cyan = np.array([150, 230, 255], dtype=np.uint8)
        d_rgb[eye_mask] = np.maximum(d_rgb[eye_mask], ice_cyan)
        e_arr[eye_mask] = 255
        # Guarantee zero stray emissive on sculpted silver face / forehead / collar (X<430, Y<380)
        e_arr[:380, :430] = 0
        print(f"  [CH11_00] True 3D eye lens lit pixels: {int(eye_mask.sum())}, Face/Forehead stray emissive: {int(e_arr[:380, :430].max())}")

    d_out = np.dstack([d_rgb, np.full((H, W), 255, dtype=np.uint8)])
    raoe_out = np.stack([r_arr, ao_arr, e_arr], axis=-1)

    return (
        Image.fromarray(d_out, "RGBA"),
        n_img,
        Image.fromarray(raoe_out, "RGB"),
        Image.fromarray(g_rgb, "RGB"),
    )


def main():
    print("=== Building Clean Authoritative Elita One Textures ===")
    ch00_d, ch00_n, ch00_raoe, ch00_glow = build_sheet(
        "T_CH11_00_D.png", "T_CH11_00_N.png", "T_CH11_00_R.png", "T_CH11_00_O.png", "MI_CH11_00_glow.tga.png", is_ch00=True
    )
    ch01_d, ch01_n, ch01_raoe, _ = build_sheet(
        "T_CH11_01_D.png", "T_CH11_01_N.png", "T_CH11_01_R.png", "T_CH11_01_O.png", "MI_CH11_01_glow.tga.png"
    )
    vh00_d, vh00_n, vh00_raoe, _ = build_sheet(
        "T_VH11_00_D.png", "T_VH11_00_N.png", "T_VH11_00_R.png", "T_VH11_00_O.png", "mat_vh0_glow.tga.png"
    )
    vh01_d, vh01_n, vh01_raoe, _ = build_sheet(
        "T_VH11_01_D.png", "T_VH11_01_N.png", "T_VH11_01_R.png", "T_VH11_01_O.png", "mat_vh1_glow.tga.png"
    )

    # 1. Robot Submesh[0] main textures (1024x1024)
    main_diff_1024 = ch00_d.resize((1024, 1024), Image.LANCZOS)
    main_norm_1024 = ch00_n.resize((1024, 1024), Image.LANCZOS)
    main_raoe_1024 = ch00_raoe.resize((1024, 1024), Image.NEAREST)
    main_glow_1024 = ch00_glow.resize((1024, 1024), Image.BILINEAR)

    main_diff_1024.save(OUT_DIR / "elita_main_diffuse.png")
    main_norm_1024.save(OUT_DIR / "elita_main_normal.png")
    main_raoe_1024.save(OUT_DIR / "elita_main_raoe.png")
    print("[✓] Saved clean elita_main_diffuse/normal/raoe (1024x1024)")

    # 2. Combined tform_misc_A (2048x2048):
    #    Top Half (Y: 0..1024)    = [1024x1024 VH00_D | 1024x1024 VH01_D]  (Vehicle Mode)
    #    Bottom Half (Y: 1024..2048) = 2048x1024 CH11_01_D                 (Robot Submesh[1])
    tform_diff = Image.new("RGBA", (2048, 2048))
    tform_diff.paste(vh00_d.resize((1024, 1024), Image.LANCZOS), (0, 0))
    tform_diff.paste(vh01_d.resize((1024, 1024), Image.LANCZOS), (1024, 0))
    tform_diff.paste(ch01_d.resize((2048, 1024), Image.LANCZOS), (0, 1024))
    tform_diff.save(OUT_DIR / "elita_tform_misc_diffuse.png")
    # Also save elita_veh_atlas_diffuse.png alias
    tform_diff.save(OUT_DIR / "elita_veh_atlas_diffuse.png")
    print("[✓] Saved unified elita_tform_misc_diffuse.png (2048x2048: Top=[VH00|VH01], Bottom=CH11_01)")

    # 3. Combined tform_misc_NM (1024x1024):
    #    Top Half (Y: 0..512)     = [512x512 VH00_N | 512x512 VH01_N]
    #    Bottom Half (Y: 512..1024) = 1024x512 CH11_01_N
    tform_norm = Image.new("RGBA", (1024, 1024))
    tform_norm.paste(vh00_n.resize((512, 512), Image.LANCZOS), (0, 0))
    tform_norm.paste(vh01_n.resize((512, 512), Image.LANCZOS), (512, 0))
    tform_norm.paste(ch01_n.resize((1024, 512), Image.LANCZOS), (0, 512))
    tform_norm.save(OUT_DIR / "elita_tform_misc_normal.png")
    tform_norm.save(OUT_DIR / "elita_veh_atlas_normal.png")
    print("[✓] Saved unified elita_tform_misc_normal.png (1024x1024: Top=[VH00|VH01], Bottom=CH11_01)")

    # 4. Combined main_tform_misc_RAOE (1024x2048):
    #    Top Half (X: 0..1024, Y: 0..1024)         = 1024x1024 CH11_00_RAOE (Robot Submesh[0] — full 1024px vertical accuracy for 3D eyes!)
    #    Bottom-Left (X: 0..512, Y: 1024..2048)    = 512x1024  CH11_01_RAOE (Robot Submesh[1])
    #    Bottom-Right (X: 512..1024, Y: 1024..2048)= [256x1024 VH00_RAOE | 256x1024 VH01_RAOE] (Vehicle Mode)
    comb_raoe = Image.new("RGB", (1024, 2048))
    comb_raoe.paste(main_raoe_1024, (0, 0))
    comb_raoe.paste(ch01_raoe.resize((512, 1024), Image.NEAREST), (0, 1024))
    comb_raoe.paste(vh00_raoe.resize((256, 1024), Image.NEAREST), (512, 1024))
    comb_raoe.paste(vh01_raoe.resize((256, 1024), Image.NEAREST), (768, 1024))
    comb_raoe.save(OUT_DIR / "elita_main_tform_misc_raoe.png")
    print("[✓] Saved unified elita_main_tform_misc_raoe.png (1024x2048 3-region Kabam RAOE atlas)")

    # 5. Sync single-sheet preview textures into Unity project Assets/ElitaOne/
    if UNITY_DIR.is_dir():
        main_diff_1024.save(UNITY_DIR / "cha_elita_one_main_a.png")
        main_norm_1024.save(UNITY_DIR / "cha_elita_one_main_NM.png")
        main_raoe_1024.save(UNITY_DIR / "cha_elita_one_main_RAOE.png")
        main_glow_1024.save(UNITY_DIR / "cha_elita_one_main_Emission.png")
        ch01_d.resize((1024, 1024), Image.LANCZOS).save(UNITY_DIR / "cha_elita_one_vh_a.png")
        ch01_n.resize((1024, 1024), Image.LANCZOS).save(UNITY_DIR / "cha_elita_one_vh_NM.png")
        comb_raoe.save(UNITY_DIR / "cha_elita_one_main_tform_misc_RAOE.png")
        print("[✓] Synced clean preview textures to Unity Assets/ElitaOne/")


if __name__ == "__main__":
    main()
