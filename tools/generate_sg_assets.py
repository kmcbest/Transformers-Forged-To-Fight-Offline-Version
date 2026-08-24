#!/usr/bin/env python3
"""
generate_sg_assets.py

Automated asset extraction and procedural recoloring tool for Shattered Glass
Optimus Prime (倾天柱). Extracts base G1 mold assets from a user-supplied official
Kabam 9.2.0 APK, applies high-vibrancy SG shaders/textures, and generates Unity 2020
AssetBundles and UI portraits for offline builds.

Usage:
    python tools/generate_sg_assets.py --input "path/to/com.kabam.bigrobot_9.2.0.apk"
"""

import argparse
import glob
import os
import sys
import zipfile
from pathlib import Path
from PIL import Image
import numpy as np

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)


def generate_sg_assets(apk_path: str, output_dir: str = "assets_redeco") -> None:
    apk_file = Path(apk_path)
    if not apk_file.is_file():
        raise FileNotFoundError(f"Input APK file not found: {apk_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Extracting base assets from: {apk_file.name} ...")

    with zipfile.ZipFile(apk_file, "r") as z:
        n_bundle_data = z.read("assets/assetpack/nemesisprime_gs_voyager2015_odr/nemesisprime_gs_voyager2015.assetbundle")
        m_bundle_data = z.read("assets/assetpack/ultramagnus_gs_leader_odr/ultramagnus_gs_leader.assetbundle")
        p_large_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_nemesis_gs_large.png")
        p_small_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_nemesis_gs_small.jpg")
        p_quest_bytes = z.read("assets/assetpack/questboard_odr/questboard/portrait_optimus_gs_quest.png")

    n_env = UnityPy.load(n_bundle_data)
    m_env = UnityPy.load(m_bundle_data)

    n_main_img = None
    n_wpns_img = None
    m_main_img = None

    for obj in n_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_nemesisprime_gs_voyager2015_main_a":
                n_main_img = obj.read().image
            elif tname == "cha_nemesisprime_gs_voyager2015_wpns_a":
                n_wpns_img = obj.read().image

    for obj in m_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_ultramagnus_gs_leader_main_a":
                m_main_img = obj.read().image

    print("[*] Processing high-fidelity Shattered Glass texture maps...")

    n_arr = np.array(n_main_img.convert("RGBA"), dtype=np.float32)
    nr, ng, nb, na = n_arr[:, :, 0], n_arr[:, :, 1], n_arr[:, :, 2], n_arr[:, :, 3]

    m_arr = np.array(m_main_img.convert("RGBA"), dtype=np.float32)
    mr, mg, mb, ma = m_arr[:, :, 0], m_arr[:, :, 1], m_arr[:, :, 2], m_arr[:, :, 3]

    lum = (nr * 0.299 + ng * 0.587 + nb * 0.114) / 255.0

    # Masks
    is_window_optics = (nr > 85) & (ng < 65) & (nb < 65)
    is_metal_silver = (lum > 0.40) & (~is_window_optics)
    is_blue_segment = (mb > 100) & (mr < 80)
    is_pure_navy = is_blue_segment & (lum < 0.25) & (~is_metal_silver) & (~is_window_optics)

    # Colors
    purple_r = np.clip(lum * 195.0 + 40.0, 0, 255)
    purple_g = np.clip(lum * 20.0 + 5.0, 0, 255)
    purple_b = np.clip(lum * 255.0 + 40.0, 0, 255)

    navy_r = np.clip(lum * 35.0 + 8.0, 0, 255)
    navy_g = np.clip(lum * 65.0 + 15.0, 0, 255)
    navy_b = np.clip(lum * 130.0 + 25.0, 0, 255)

    silver_r = np.clip(lum * 220.0 + 30.0, 0, 255)
    silver_g = np.clip(lum * 225.0 + 30.0, 0, 255)
    silver_b = np.clip(lum * 235.0 + 35.0, 0, 255)

    yellow_r = np.clip(lum * 60.0 + 240.0, 0, 255)
    yellow_g = np.clip(lum * 60.0 + 225.0, 0, 255)
    yellow_b = np.clip(lum * 10.0 + 15.0, 0, 255)

    final_r = np.where(is_window_optics, yellow_r,
              np.where(is_metal_silver, silver_r,
              np.where(is_pure_navy, navy_r, purple_r)))

    final_g = np.where(is_window_optics, yellow_g,
              np.where(is_metal_silver, silver_g,
              np.where(is_pure_navy, navy_g, purple_g)))

    final_b = np.where(is_window_optics, yellow_b,
              np.where(is_metal_silver, silver_b,
              np.where(is_pure_navy, navy_b, purple_b)))

    final_main_img = Image.fromarray(np.stack([final_r, final_g, final_b, na], axis=-1).astype(np.uint8))
    final_main_img.save(out_dir / "cha_optimusprime_sg_main_a.png")

    # Weapons Texture
    w_arr = np.array(n_wpns_img.convert("RGBA"), dtype=np.float32)
    wr, wg, wb, wa = w_arr[:, :, 0], w_arr[:, :, 1], w_arr[:, :, 2], w_arr[:, :, 3]
    wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0

    is_blade = (wlum > 0.25)
    sg_axe_r = np.clip(wlum * 195.0 + 40.0, 0, 255)
    sg_axe_g = np.clip(wlum * 20.0 + 5.0, 0, 255)
    sg_axe_b = np.clip(wlum * 255.0 + 35.0, 0, 255)

    sg_gun_r = np.clip(wlum * 140.0 + 35.0, 0, 255)
    sg_gun_g = np.clip(wlum * 145.0 + 35.0, 0, 255)
    sg_gun_b = np.clip(wlum * 155.0 + 40.0, 0, 255)

    w_out_r = np.where(is_blade, sg_axe_r, sg_gun_r)
    w_out_g = np.where(is_blade, sg_axe_g, sg_gun_g)
    w_out_b = np.where(is_blade, sg_axe_b, sg_gun_b)

    final_wpns_img = Image.fromarray(np.stack([w_out_r, w_out_g, w_out_b, wa], axis=-1).astype(np.uint8))
    final_wpns_img.save(out_dir / "cha_optimusprime_sg_wpns_a.png")

    print("[*] Rebuilding UnityFS AssetBundle for Unity 2020.3.31f1...")

    for obj in n_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_nemesisprime_gs_voyager2015_main_a":
                data_obj = obj.read()
                data_obj.image = final_main_img
                data_obj.save()
            elif tname == "cha_nemesisprime_gs_voyager2015_wpns_a":
                data_obj = obj.read()
                data_obj.image = final_wpns_img
                data_obj.save()

    bf = n_env.file
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"

    sg_bundle_bytes = bf.save(packer="lz4")
    (out_dir / "optimusprime_sg_voyager2015.assetbundle").write_bytes(sg_bundle_bytes)

    print("[*] Generating UI Portraits...")

    def make_portrait(raw_bytes: bytes, out_name: str, is_jpg: bool = False):
        import io
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        arr = np.array(img, dtype=np.float32)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        plum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0

        is_glow = (r > 120) & (g < 85) & (b < 85)
        is_cyan = (g > 100) & (g > 100) & (r < 90)

        pr = plum * 140.0 + 30.0
        pg = plum * 40.0 + 10.0
        pb = plum * 180.0 + 45.0

        res_r = np.where(is_glow | is_cyan, np.clip(plum * 100.0 + 220.0, 0, 255), pr * 0.7 + r * 0.3)
        res_g = np.where(is_glow | is_cyan, np.clip(plum * 100.0 + 210.0, 0, 255), pg * 0.7 + g * 0.3)
        res_b = np.where(is_glow | is_cyan, np.clip(plum * 20.0 + 30.0, 0, 255), pb * 0.7 + b * 0.3)

        res_img = Image.fromarray(np.stack([np.clip(res_r, 0, 255), np.clip(res_g, 0, 255), np.clip(res_b, 0, 255), a], axis=-1).astype(np.uint8))
        if is_jpg:
            res_img.convert("RGB").save(out_dir / out_name, quality=95)
        else:
            res_img.save(out_dir / out_name)

    make_portrait(p_large_bytes, "portrait_optimus_sg_large.png", False)
    make_portrait(p_small_bytes, "portrait_optimus_sg_small.jpg", True)
    make_portrait(p_quest_bytes, "portrait_optimus_sg_quest.png", False)
    make_portrait(p_large_bytes, "optimus_sg.png", False)

    print(f"[+] All Shattered Glass assets successfully generated in: {out_dir}/")


def find_default_apk() -> str | None:
    candidates = glob.glob("com.kabam.bigrobot*.apk") + glob.glob("*.apk")
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(description="Generate Shattered Glass Optimus Prime (倾天柱) assets.")
    parser.add_argument("--input", "-i", default=find_default_apk(), help="Path to base Kabam 9.2.0 APK")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory (default: assets_redeco)")
    args = parser.parse_args()

    if not args.input:
        print("Error: No base APK specified. Provide one with --input path/to/com.kabam.bigrobot_9.2.0.apk")
        sys.exit(1)

    generate_sg_assets(args.input, args.output)


if __name__ == "__main__":
    main()
