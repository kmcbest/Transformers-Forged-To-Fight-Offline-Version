#!/usr/bin/env python3
"""
generate_starsaber_assets.py

Complete composite grafting pipeline for Autobot Supreme Commander Star Saber (史达).
Performs:
1. Physical 3D Mesh grafting: Injects Motormaster's Saber Blade into weapon slot
2. AnimatorOverrideController fight grafting: Injects Motormaster's sword combo & S1,
   Windblade's S2 AnimationClip, and retains Jetfire's Heavy & S3
3. MoveSet MoveInfo rewiring for hitboxes and damage frames
4. Procedural Victory color synthesis (Ceramic White, Victory Red, Cobalt Blue, Imperial Gold)
5. Single-pass unified serialization ensuring 100% persistence
6. Deep CAB & namespace isolation (CAB-7e3f890123456789abcdef0123456789)

Usage:
    python tools/generate_starsaber_assets.py --input "path/to/com.kabam.bigrobot_9.2.0.apk"
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


def generate_starsaber_assets(apk_path: str, output_dir: str = "assets_redeco") -> None:
    apk_file = Path(apk_path)
    if not apk_file.is_file():
        raise FileNotFoundError(f"Input APK file not found: {apk_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Extracting base components from: {apk_file.name} ...")

    with zipfile.ZipFile(apk_file, "r") as z:
        j_bundle_data = z.read("assets/assetpack/jetfire_gs_leader2014_odr/jetfire_gs_leader2014.assetbundle")
        m_bundle_data = z.read("assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle")
        w_bundle_data = z.read("assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle")
        p_large_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_large.png")
        p_small_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_small.jpg")
        p_quest_bytes = p_large_bytes

    j_env = UnityPy.load(j_bundle_data)
    m_env = UnityPy.load(m_bundle_data)
    w_env = UnityPy.load(w_bundle_data)

    print("[*] Synthesizing Star Saber (史达) texture maps...")

    j_main_img = None
    for obj in j_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_jetfire_gs_leader2014_main_a":
                j_main_img = obj.read().image

    m_wpns_img = None
    for obj in m_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if "wpns_a" in tname:
                m_wpns_img = obj.read().image

    # 1. Main Body Texture Recolor (Star Saber Victory Scheme)
    j_arr = np.array(j_main_img.convert("RGBA"), dtype=np.float32)
    jr, jg, jb, ja = j_arr[:, :, 0], j_arr[:, :, 1], j_arr[:, :, 2], j_arr[:, :, 3]
    lum = (jr * 0.299 + jg * 0.587 + jb * 0.114) / 255.0

    is_red_accents = (jr > 110) & (jg < 70) & (jb < 70)
    is_black_metals = (lum < 0.25)
    is_white_armor = (lum >= 0.25) & (~is_red_accents)

    # Star Saber Colors:
    ss_red_r = np.clip(lum * 180.0 + 75.0, 0, 255)
    ss_red_g = np.clip(lum * 25.0 + 5.0, 0, 255)
    ss_red_b = np.clip(lum * 35.0 + 10.0, 0, 255)

    ss_blue_r = np.clip(lum * 20.0 + 8.0, 0, 255)
    ss_blue_g = np.clip(lum * 60.0 + 25.0, 0, 255)
    ss_blue_b = np.clip(lum * 180.0 + 75.0, 0, 255)

    ss_white_r = np.clip(lum * 140.0 + 115.0, 0, 255)
    ss_white_g = np.clip(lum * 140.0 + 115.0, 0, 255)
    ss_white_b = np.clip(lum * 145.0 + 115.0, 0, 255)

    final_r = np.where(is_red_accents, ss_red_r, np.where(is_black_metals, ss_blue_r, ss_white_r))
    final_g = np.where(is_red_accents, ss_red_g, np.where(is_black_metals, ss_blue_g, ss_white_g))
    final_b = np.where(is_red_accents, ss_red_b, np.where(is_black_metals, ss_blue_b, ss_white_b))

    final_main_img = Image.fromarray(np.stack([final_r, final_g, final_b, ja], axis=-1).astype(np.uint8))
    final_main_img.save(out_dir / "cha_starsaber_gs_leader2014_main_a.png")

    # 2. Saber Blade Weapons Texture Synthesis
    w_arr = np.array(m_wpns_img.convert("RGBA"), dtype=np.float32)
    wr, wg, wb, wa = w_arr[:, :, 0], w_arr[:, :, 1], w_arr[:, :, 2], w_arr[:, :, 3]
    wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0

    saber_blade_r = np.clip(wlum * 180.0 + 75.0, 0, 255)
    saber_blade_g = np.clip(wlum * 195.0 + 60.0, 0, 255)
    saber_blade_b = np.clip(wlum * 240.0 + 25.0, 0, 255)

    final_wpns_img = Image.fromarray(np.stack([saber_blade_r, saber_blade_g, saber_blade_b, wa], axis=-1).astype(np.uint8))
    final_wpns_img.save(out_dir / "cha_starsaber_gs_leader2014_wpns_a.png")

    print("[*] Extracting Motormaster Saber Blade Mesh...")
    sword_mesh_tree = None
    for obj in m_env.objects:
        if obj.type.name == "Mesh" and "sword" in obj.read_typetree().get("m_Name", ""):
            sword_mesh_tree = obj.read_typetree()
            sword_mesh_tree["m_Name"] = "cha_starsaber_gs_leader2014_wpns_sword"
            print("[+] Found Motormaster Saber Blade Mesh")
            break

    print("[*] Extracting Windblade S2 AnimationClip...")
    wb_s2_clip_tree = None
    for obj in w_env.objects:
        if obj.type.name == "AnimationClip" and "attackSpecial_02" in obj.read_typetree().get("m_Name", ""):
            wb_s2_clip_tree = obj.read_typetree()
            print(f"[+] Found Windblade S2 Clip: {wb_s2_clip_tree.get('m_Name')}")
            break

    print("[*] Executing Unified Single-Pass Grafting & Deep CAB Isolation...")

    bf = list(j_env.files.values())[0]
    old_cab = "CAB-b8c9c95336c492304a83824d5971bea0"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-7e3f890123456789abcdef0123456789"
    print(f"[*] Deep remapping CAB: {old_cab} -> {new_cab}")

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

    WB_S2_PATHID = -6524404075124180520

    for obj in j_env.objects:
        if obj.path_id == -4439679313609908059 and obj.type.name == "Mesh" and sword_mesh_tree is not None:
            tree = sword_mesh_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Saber Blade Mesh into weapon slot")
        elif obj.path_id == 1268969612974345036 and wb_s2_clip_tree is not None:
            tree = wb_s2_clip_tree
            WB_S2_PATHID = obj.path_id
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Injected Windblade S2 AnimationClip at PathID: {WB_S2_PATHID}")
        elif obj.path_id == -8402565767957608701 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            # Motormaster Sword combos (FileID 2 = common animation bundle in Jetfire)
            clips[41]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4980757935915932854}  # Light 01
            clips[42]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 6308122467145514604}   # Light 02
            clips[43]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4106831893816218441}  # Light 03
            clips[44]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -705967800912522861}   # Light 04
            clips[45]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 7146863003282264883}   # Medium 01
            clips[46]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 7146863003282264883}   # Medium 02
            # S1 -> Motormaster S1 Sword Thrust
            clips[51]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -3948795660449728024}  # Motormaster S1
            # S2 -> Windblade S2 Cyclone Dance
            clips[52]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": WB_S2_PATHID}           # Windblade S2
            # S3 -> Keeps Jetfire S3 (clips[53])
            # Heavy -> Keeps Jetfire Heavy (clips[40])
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully grafted AnimatorOverrideController fight clips!")
        elif obj.path_id == 2601823321879744519 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            if len(moves) >= 10:
                moves[0] = {"_name": "move_sword_attack_light_01", "_animStateName": "Base.LightAttack01", "_asset": {"m_FileID": 3, "m_PathID": -1283304507747283112}}
                moves[1] = {"_name": "move_sword_attack_light_02", "_animStateName": "Base.LightAttack02", "_asset": {"m_FileID": 3, "m_PathID": 7616440351077033282}}
                moves[2] = {"_name": "move_sword_attack_light_03", "_animStateName": "Base.LightAttack03", "_asset": {"m_FileID": 3, "m_PathID": -3329254882358104680}}
                moves[3] = {"_name": "move_sword_attack_light_04", "_animStateName": "Base.LightAttack04", "_asset": {"m_FileID": 3, "m_PathID": 4145453135915101152}}
                moves[4] = {"_name": "move_sword_attack_medium_01", "_animStateName": "Base.MediumAttack01", "_asset": {"m_FileID": 3, "m_PathID": -1389778547757567769}}
                moves[5] = {"_name": "move_sword_attack_medium_02", "_animStateName": "Base.MediumAttack02", "_asset": {"m_FileID": 3, "m_PathID": -3898379380470346085}}
                moves[6] = {"_name": "move_motormaster_special_01", "_animStateName": "Base.SpecialAttack01", "_asset": {"m_FileID": 3, "m_PathID": 8279538491675176653}}
                moves[7] = {"_name": "move_windblade_special_02", "_animStateName": "Base.SpecialAttack02", "_asset": {"m_FileID": 3, "m_PathID": -6524404075124180520}}
                moves[8] = {"_name": "move_sword_block_react", "_animStateName": "Base.BlockReact", "_asset": {"m_FileID": 3, "m_PathID": 2656533506074151531}}
                moves[9] = {"_name": "move_sword_block_react", "_animStateName": "Base.BlockReactRanged", "_asset": {"m_FileID": 3, "m_PathID": 6843684539569461767}}
                tree["_moves"] = moves
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
                print("[+] Successfully re-wired MoveSet with Motormaster Sword Combo, S1, and Windblade S2!")
        elif obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_jetfire_gs_leader2014_main_a":
                data_obj = obj.read()
                data_obj.image = final_main_img
                data_obj.save()
            elif tname == "cha_jetfire_gs_leader2014_wpns_a":
                data_obj = obj.read()
                data_obj.image = final_wpns_img
                data_obj.save()
            else:
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/starsaber_gs_leader2014_odr/starsaber_gs_leader2014.assetbundle"
            tree["m_AssetBundleName"] = "data/starsaber_gs_leader2014_odr/starsaber_gs_leader2014.assetbundle"
            new_container = []
            for k, v in tree.get("m_Container", []):
                new_k = k.replace("jetfire_gs_leader2014", "starsaber_gs_leader2014")
                new_container.append((new_k, v))
            tree["m_Container"] = new_container
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
        elif obj.type.name == "GameObject":
            tree = obj.read_typetree()
            gname = tree.get("m_Name", "")
            if "jetfire" in gname.lower():
                tree["m_Name"] = gname.replace("Jetfire", "StarSaber").replace("jetfire", "starsaber")
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
        else:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except Exception:
                pass

    new_files = {}
    for subfname, subf in bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf

    bf.files = new_files
    bf.version = 7
    bf.version_engine = "2020.3.31f1"
    bf.version_player = "5.x.x"

    ss_bundle_bytes = bf.save(packer="lz4")
    (out_dir / "starsaber_gs_leader2014.assetbundle").write_bytes(ss_bundle_bytes)

    print("[*] Generating Star Saber UI Portraits...")

    def make_portrait(raw_bytes: bytes, out_name: str, is_jpg: bool = False):
        import io
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        arr = np.array(img, dtype=np.float32)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        plum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0

        pr = np.clip(plum * 180.0 + 75.0, 0, 255)
        pg = np.clip(plum * 140.0 + 35.0, 0, 255)
        pb = np.clip(plum * 220.0 + 45.0, 0, 255)

        is_red = (r > 120) & (g < 80) & (b < 80)
        res_r = np.where(is_red, np.clip(plum * 100.0 + 220.0, 0, 255), pr * 0.6 + r * 0.4)
        res_g = np.where(is_red, np.clip(plum * 40.0 + 30.0, 0, 255), pg * 0.6 + g * 0.4)
        res_b = np.where(is_red, np.clip(plum * 40.0 + 40.0, 0, 255), pb * 0.6 + b * 0.4)

        res_img = Image.fromarray(np.stack([np.clip(res_r, 0, 255), np.clip(res_g, 0, 255), np.clip(res_b, 0, 255), a], axis=-1).astype(np.uint8))
        if is_jpg:
            res_img.convert("RGB").save(out_dir / out_name, quality=95)
        else:
            res_img.save(out_dir / out_name)

    make_portrait(p_large_bytes, "portrait_starsaber_large.png", False)
    make_portrait(p_small_bytes, "portrait_starsaber_small.jpg", True)
    make_portrait(p_quest_bytes, "portrait_starsaber_quest.png", False)
    make_portrait(p_large_bytes, "starsaber.png", False)

    print(f"[+] Star Saber (史达) complete composite assets successfully generated in: {out_dir}/")


def find_default_apk() -> str | None:
    candidates = glob.glob("com.kabam.bigrobot*.apk") + glob.glob("*.apk")
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(description="Generate Star Saber (史达) complete composite assets.")
    parser.add_argument("--input", "-i", default=find_default_apk(), help="Path to base Kabam 9.2.0 APK")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory (default: assets_redeco)")
    args = parser.parse_args()

    if not args.input:
        print("Error: No base APK specified. Provide one with --input path/to/com.kabam.bigrobot_9.2.0.apk")
        sys.exit(1)

    generate_starsaber_assets(args.input, args.output)


if __name__ == "__main__":
    main()
