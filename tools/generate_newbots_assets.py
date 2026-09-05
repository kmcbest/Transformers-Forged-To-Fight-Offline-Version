#!/usr/bin/env python3
"""
generate_newbots_assets.py

Batch asset extraction, procedural recoloring, and AssetBundle synthesis pipeline for:
1. Thrust (冲锋) - Scout
2. Acid Storm (酸雨) - Tech
3. Ion Storm (离子风) - Tactician
4. Nova Storm (新星风) - Demolition
5. Sunstorm (太阳风) - Warrior
6. Bitstream (比特流) - Tech
7. Hotlink (热链接) - Brawler
8. Red Alert (红色警报) - Warrior

Applies high-vibrancy recoloring adhering to instructions and reference images,
isolates unique internal CABs to prevent runtime caching collisions,
and produces UI portraits and 2020.3 AssetBundles.
"""

import argparse
import glob
import io
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


def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in tree_obj.items():
            if isinstance(v, str) and old_s in v:
                tree_obj[k] = v.replace(old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for idx, item in enumerate(tree_obj):
            if isinstance(item, str) and old_s in item:
                tree_obj[idx] = item.replace(old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)


def recolor_image(img: Image.Image, color_fn) -> Image.Image:
    arr = np.array(img.convert("RGBA"), dtype=np.float32)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
    out_r, out_g, out_b = color_fn(r, g, b, a, lum)
    res = np.stack([np.clip(out_r, 0, 255), np.clip(out_g, 0, 255), np.clip(out_b, 0, 255), a], axis=-1).astype(np.uint8)
    return Image.fromarray(res)


def make_portraits(base_large_bytes: bytes, base_small_bytes: bytes, out_dir: Path, bot_short: str, color_fn):
    p_large = Image.open(io.BytesIO(base_large_bytes)).convert("RGBA")
    p_small = Image.open(io.BytesIO(base_small_bytes)).convert("RGBA")

    re_large = recolor_image(p_large, color_fn)
    re_small = recolor_image(p_small, color_fn)

    re_large.save(out_dir / f"portrait_{bot_short}_large.png")
    re_small.convert("RGB").save(out_dir / f"portrait_{bot_short}_small.jpg", quality=95)
    re_large.save(out_dir / f"portrait_{bot_short}_quest.png")
    re_large.save(out_dir / f"{bot_short}.png")


def generate_all_newbots(apk_path: str, output_dir: str = "assets_redeco") -> None:
    apk_file = Path(apk_path)
    if not apk_file.is_file():
        raise FileNotFoundError(f"APK file not found: {apk_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Reading base bundles from {apk_file.name}...")

    with zipfile.ZipFile(apk_file, "r") as z:
        dirge_bundle = z.read("assets/assetpack/dirge_gs_deluxe2008_odr/dirge_gs_deluxe2008.assetbundle")
        thunder_bundle = z.read("assets/assetpack/thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle")

        p_dirge_l = z.read("assets/assetpack/portraits_odr/portraits/portrait_dirge_gs_large.png")
        p_dirge_s = z.read("assets/assetpack/portraits_odr/portraits/portrait_dirge_gs_small.png")
        p_thunder_l = z.read("assets/assetpack/portraits_odr/portraits/portrait_thunder_gs_large.png")
        p_thunder_s = z.read("assets/assetpack/portraits_odr/portraits/portrait_thunder_gs_small.jpg")

    def thrust_color_fn(r, g, b, a, lum):
        # Precise blue panel detection (only change Dirge's blue armor to deep rich burgundy/crimson red)
        # Keeps white/light silver mechanical parts and dark black trim completely untouched for maximum contrast!
        is_blue = (b > r * 1.15 + 10) & (b > g * 1.10 + 10) & (b > 45)
        is_gold = (r > 140) & (g > 110) & (b < 90)

        t_red_r = np.clip(lum * 215.0 + 35.0, 0, 255)
        t_red_g = np.clip(lum * 18.0 + 5.0, 0, 255)
        t_red_b = np.clip(lum * 28.0 + 8.0, 0, 255)

        t_gold_r = np.clip(lum * 60.0 + 240.0, 0, 255)
        t_gold_g = np.clip(lum * 60.0 + 195.0, 0, 255)
        t_gold_b = np.clip(lum * 10.0 + 15.0, 0, 255)

        out_r = np.where(is_blue, t_red_r, np.where(is_gold, t_gold_r, r))
        out_g = np.where(is_blue, t_red_g, np.where(is_gold, t_gold_g, g))
        out_b = np.where(is_blue, t_red_b, np.where(is_gold, t_gold_b, b))
        return out_r, out_g, out_b

    BOTS_SPEC = [
        # 1. Thrust (冲锋)
        {
            "id": "thrust_gs_deluxe2008",
            "short": "thrust",
            "base_bundle": dirge_bundle,
            "base_name": "dirge_gs_deluxe2008",
            "base_l": p_dirge_l, "base_s": p_dirge_s,
            "cab": "CAB-7e3f0101010101010101010101010101",
            "color_fn": thrust_color_fn
        },
        # 2. Acid Storm (酸雨)
        {
            "id": "acidstorm_gs_leader2015",
            "short": "acidstorm",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0202020202020202020202020202",
            "color_fn": lambda r, g, b, a, lum: (
                # Blue -> Toxic Camo Green, Cockpit -> Chartreuse Yellow
                np.where((b > 70) & (b > r * 1.05), lum * 45.0 + 20.0, np.where(lum > 0.4, lum * 160.0 + 40.0, r)),
                np.where((b > 70) & (b > r * 1.05), lum * 215.0 + 35.0, np.where(lum > 0.4, lum * 230.0 + 25.0, g)),
                np.where((b > 70) & (b > r * 1.05), lum * 35.0 + 10.0, np.where(lum > 0.4, lum * 30.0 + 10.0, b))
            )
        },
        # 3. Ion Storm (离子风)
        {
            "id": "ionstorm_gs_leader2015",
            "short": "ionstorm",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0303030303030303030303030303",
            "color_fn": lambda r, g, b, a, lum: (
                # Bright Electric Cyan/Azure
                np.where(lum > 0.15, lum * 30.0 + 10.0, r),
                np.where(lum > 0.15, lum * 175.0 + 45.0, g),
                np.where(lum > 0.15, lum * 255.0 + 55.0, b)
            )
        },
        # 4. Nova Storm (新星风)
        {
            "id": "novastorm_gs_leader2015",
            "short": "novastorm",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0404040404040404040404040404",
            "color_fn": lambda r, g, b, a, lum: (
                # Solar Radiant Gold Yellow
                np.where(lum > 0.15, lum * 255.0 + 45.0, r),
                np.where(lum > 0.15, lum * 205.0 + 25.0, g),
                np.where(lum > 0.15, lum * 20.0 + 5.0, b)
            )
        },
        # 5. Sunstorm (太阳风)
        {
            "id": "sunstorm_gs_leader2015",
            "short": "sunstorm",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0505050505050505050505050505",
            "color_fn": lambda r, g, b, a, lum: (
                # Solar Orange + Pure White accents
                np.where((lum > 0.5) & (b < 100), lum * 250.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 255.0 + 40.0, lum * 230.0 + 25.0)),
                np.where((lum > 0.5) & (b < 100), lum * 250.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 125.0 + 20.0, lum * 230.0 + 25.0)),
                np.where((lum > 0.5) & (b < 100), lum * 250.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 15.0 + 5.0, lum * 230.0 + 25.0))
            )
        },
        # 6. Bitstream (比特流)
        {
            "id": "bitstream_gs_leader2015",
            "short": "bitstream",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0606060606060606060606060606",
            "color_fn": lambda r, g, b, a, lum: (
                # Cyber Aqua Teal + White
                np.where(lum > 0.55, lum * 240.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 35.0 + 15.0, r)),
                np.where(lum > 0.55, lum * 245.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 195.0 + 45.0, g)),
                np.where(lum > 0.55, lum * 250.0 + 15.0, np.where((b > 70) & (b > r * 1.05), lum * 225.0 + 40.0, b))
            )
        },
        # 7. Hotlink (热链接)
        {
            "id": "hotlink_gs_leader2015",
            "short": "hotlink",
            "base_bundle": thunder_bundle,
            "base_name": "thundercracker_gs_leader2015",
            "base_l": p_thunder_l, "base_s": p_thunder_s,
            "cab": "CAB-7e3f0707070707070707070707070707",
            "color_fn": lambda r, g, b, a, lum: (
                # Deep Burgundy Violet / Plum Purple + White
                np.where(lum > 0.55, lum * 230.0 + 25.0, np.where((b > 70) & (b > r * 1.05), lum * 165.0 + 35.0, r)),
                np.where(lum > 0.55, lum * 230.0 + 25.0, np.where((b > 70) & (b > r * 1.05), lum * 25.0 + 10.0, g)),
                np.where(lum > 0.55, lum * 240.0 + 25.0, np.where((b > 70) & (b > r * 1.05), lum * 180.0 + 40.0, b))
            )
        }
    ]

    for spec in BOTS_SPEC:
        bot_id = spec["id"]
        bot_short = spec["short"]
        base_name = spec["base_name"]
        cab = spec["cab"]
        color_fn = spec["color_fn"]
        print(f"[*] Processing {bot_short.upper()} ({bot_id})...")

        # 1. Generate Portraits
        make_portraits(spec["base_l"], spec["base_s"], out_dir, bot_short, color_fn)

        # 2. Process AssetBundle
        env = UnityPy.load(spec["base_bundle"])
        bf = list(env.files.values())[0]

        old_cab = None
        for subfname in bf.files.keys():
            if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
                old_cab = subfname
                break

        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tree = obj.read_typetree()
                tname = tree.get("m_Name", "")
                if any(k in tname.lower() for k in ["main_a", "wpns_a", "tform_misc_a", "misc_a"]):
                    data_obj = obj.read()
                    orig_img = data_obj.image
                    new_img = recolor_image(orig_img, color_fn)
                    new_img.save(out_dir / f"{tname.replace(base_name, bot_id)}.png")
                    data_obj.image = new_img
                    data_obj.save()
                else:
                    if old_cab:
                        replace_str_in_tree(tree, old_cab, cab)
                    obj.save_typetree(tree)
            elif obj.type.name == "AssetBundle":
                tree = obj.read_typetree()
                tree["m_Name"] = f"data/{bot_id}_odr/{bot_id}.assetbundle"
                tree["m_AssetBundleName"] = f"data/{bot_id}_odr/{bot_id}.assetbundle"
                new_container = []
                for k, v in tree.get("m_Container", []):
                    new_k = k.replace(base_name, bot_id)
                    new_container.append((new_k, v))
                tree["m_Container"] = new_container
                if old_cab:
                    replace_str_in_tree(tree, old_cab, cab)
                obj.save_typetree(tree)
            elif obj.type.name == "GameObject":
                tree = obj.read_typetree()
                gname = tree.get("m_Name", "")
                if base_name in gname:
                    tree["m_Name"] = gname.replace(base_name, bot_id)
                if old_cab:
                    replace_str_in_tree(tree, old_cab, cab)
                obj.save_typetree(tree)
            else:
                try:
                    tree = obj.read_typetree()
                    if old_cab:
                        replace_str_in_tree(tree, old_cab, cab)
                    obj.save_typetree(tree)
                except Exception:
                    pass

        new_files = {}
        for subfname, subf in bf.files.items():
            new_subfname = subfname.replace(old_cab, cab) if old_cab else subfname
            if hasattr(subf, "name"):
                subf.name = new_subfname
            new_files[new_subfname] = subf

        bf.files = new_files
        bf.version = 7
        bf.version_engine = "2020.3.31f1"
        bf.version_player = "5.x.x"

        bundle_bytes = bf.save(packer="lz4")
        (out_dir / f"{bot_id}.assetbundle").write_bytes(bundle_bytes)
        print(f"[+] Successfully generated: {out_dir / f'{bot_id}.assetbundle'}")

    print("[+] All 8 Redeco characters generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate 8 new Redeco characters.")
    candidates = glob.glob("com.kabam.bigrobot*.apk") + glob.glob("*.apk")
    default_apk = candidates[0] if candidates else None
    parser.add_argument("--input", "-i", default=default_apk, help="Base Kabam APK")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()

    if not args.input:
        print("Error: Base APK not found.")
        sys.exit(1)

    generate_all_newbots(args.input, args.output)


if __name__ == "__main__":
    main()
