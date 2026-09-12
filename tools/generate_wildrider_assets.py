#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_wildrider_assets.py

Custom composite grafting pipeline for Decepticon Wildrider (莽撞).
Faction: Decepticon (霸天虎)
Class: Brawler (braw)

1. Base Body & Vehicle Mode:
   - Cloned from Prowl (prowl_gs_deluxe2016.assetbundle)
2. Combat Animation & Moveset Grafting:
   - Normal attacks (Light 1..4, Medium 1..2): Prowl (Preserved)
   - Heavy Attack: Prowl (Preserved)
   - S1: Galvatron (Galvatron_GS_attackSpecial_01 / move_galvatron_special_01)
   - S2: Motormaster (motormaster_gs_attackSpecial_02 / move_motormaster_special_02)
   - S3: Prowl (prowl_gs_delux_attackSpecial_03 / move_prowl_special_03 Preserved)
3. Visuals & Recolor:
   - Dark Charcoal / Slate Black vehicle & robot armor
   - Pure white chest plate with symmetrical Decepticon insignia and blue vent decals
   - Translucent red vehicle windows & red rocker racing stripes
   - Gunmetal gray weapons
   - Symmetrical crimson faceplate with red eye optics
"""

import argparse
import copy
import io
import os
import sys
import zipfile
from pathlib import Path
from PIL import Image

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')


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


def generate_wildrider_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = Path("extracted_apk/assets/assetpack")
    def load_bundle(rel_path: str) -> bytes:
        if (extracted / rel_path).is_file():
            return (extracted / rel_path).read_bytes()
        if apk_path and Path(apk_path).is_file():
            with zipfile.ZipFile(apk_path, "r") as z:
                return z.read(f"assets/assetpack/{rel_path}")
        raise FileNotFoundError(f"Cannot find {rel_path} in extracted_apk or {apk_path}")

    print("[*] Loading component assetbundles...")
    prowl_bytes = load_bundle("prowl_gs_deluxe2016_odr/prowl_gs_deluxe2016.assetbundle")
    galvatron_bytes = load_bundle("galvatron_gs_voyager2016_odr/galvatron_gs_voyager2016.assetbundle")
    procedural_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")

    print("[*] Parsing source bundles...")
    p_env = UnityPy.load(prowl_bytes)
    g_env = UnityPy.load(galvatron_bytes)
    proc_env = UnityPy.load(procedural_bytes)

    # 1. Extract required AnimationClips
    print("[*] Extracting external animation clips...")

    # Galvatron S1: Galvatron_GS_attackSpecial_01 (-1265828487359043164)
    clip_s1 = None
    for obj in g_env.objects:
        if obj.path_id == -1265828487359043164 and obj.type.name == "AnimationClip":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "wildrider_GS_attackSpecial_01"
            break

    if clip_s1 is None:
        raise ValueError("Could not find Galvatron S1 clip in galvatron_gs_voyager2016.assetbundle!")

    # Motormaster S2: motormaster_gs_attackSpecial_02 (-5547817616214473576)
    clip_s2 = None
    for obj in proc_env.objects:
        if obj.path_id == -5547817616214473576 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "wildrider_GS_attackSpecial_02"
            break

    if clip_s2 is None:
        raise ValueError("Could not find Motormaster S2 clip in character_anim_procedural.assetbundle!")

    print("[+] Extracted Galvatron S1 and Motormaster S2 animation clips!")

    # 2. Re-wire Prowl bundle
    print("[*] Grafting Wildrider into Prowl physical rig...")
    bf = list(p_env.files.values())[0]
    p_asset = list(p_env.assets)[0]

    old_cab = "CAB-a71826aa70cef5a62d7b7abb5cafeed6"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-wildrider2016gs00001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    PID_S1 = 991001
    PID_S2 = 991002

    new_clips = [
        (PID_S1, clip_s1),
        (PID_S2, clip_s2),
    ]

    template_clip = [o for o in p_asset.objects.values() if o.type.name == "AnimationClip"][0]

    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab)
        new_obj.save_typetree(ctree)
        p_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} new AnimationClips into Wildrider asset!")

    # Update objects in Prowl bundle
    user_main_path = out_dir / "cha_wildrider_gs_deluxe2016_main_a.png"
    user_misc_path = out_dir / "cha_wildrider_gs_deluxe2016_tform_misc_a.png"
    user_wpns_path = out_dir / "cha_wildrider_gs_deluxe2016_wpns_a.png"

    for obj in p_env.objects:
        # Fight AOC: override_Prowl_GS_Deluxe2016_fight (PathID=-8799352062880271755)
        if obj.path_id == -8799352062880271755 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])

            # Slot 4: S1 -> Galvatron S1
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
            # Slot 5: S2 -> Motormaster S2
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            # Slot 31: S3 -> Preserved original Prowl S3

            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Wildrider Fight AOC (S1=Galvatron, S2=Motormaster, S3=Prowl, Normals=Prowl)!")

        # MoveSet: PathID=4685508596578817746
        elif obj.path_id == 4685508596578817746 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])

            # [6] S1: move_galvatron_special_01
            moves[6]["_name"] = "move_galvatron_special_01"
            moves[6]["_asset"] = {"m_FileID": 6, "m_PathID": -5882940919102495494}

            # [7] S2: move_motormaster_special_02
            moves[7]["_name"] = "move_motormaster_special_02"
            moves[7]["_asset"] = {"m_FileID": 6, "m_PathID": -564276376835722605}

            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Wildrider MoveSet (moves[6]=Galvatron S1, moves[7]=Motormaster S2)!")

        # Texture2D: Load custom recolored textures
        elif obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_prowl_gs_deluxe2016_main_a" and user_main_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_main_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Wildrider main texture: {user_main_path}")
            elif tex_name == "tform_misc_A" and user_misc_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_misc_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Wildrider vehicle misc texture: {user_misc_path}")
            elif tex_name == "cha_prowl_gs_deluxe2016_wpns_a" and user_wpns_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_wpns_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Wildrider weapons texture: {user_wpns_path}")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        # AssetBundle container & preload table
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/wildrider_gs_deluxe2016_odr/wildrider_gs_deluxe2016.assetbundle"
            container = tree.get("m_Container", [])
            new_container = []
            for item in container:
                path_str = item[0].replace("prowl_gs_deluxe2016", "wildrider_gs_deluxe2016")
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container

            # Append injected clips to preload table
            preload = tree.get("m_PreloadTable", [])
            preload.append({"m_FileID": 0, "m_PathID": PID_S1})
            preload.append({"m_FileID": 0, "m_PathID": PID_S2})
            tree["m_PreloadTable"] = preload

            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Updated AssetBundle container table and preload list!")

        # Root GameObjects: Keep names intact so MatineeStage hierarchy lookups succeed
        elif obj.path_id in [-8683282172418555027, -8048857395234776728] and obj.type.name == "GameObject":
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # For stream-backed assets (AudioClip, etc.)
        elif obj.type.name in ["AudioClip"]:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # All other MonoBehaviours / Controllers
        elif obj.type.name in ["AnimatorOverrideController", "MonoBehaviour", "AnimatorController"]:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except:
                pass

    # Save rebuilt AssetBundle
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

    target_bundle = out_dir / "wildrider_gs_deluxe2016.assetbundle"
    target_bundle.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")
    print("[+] Wildrider assetbundle generation complete!")


def main():
    parser = argparse.ArgumentParser(description="Generate Wildrider (莽撞) composite assets.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_wildrider_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
