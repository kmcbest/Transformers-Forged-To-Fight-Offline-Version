#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_breakdown_assets.py

Custom composite grafting pipeline for Decepticon Breakdown (打击).
Faction: Decepticon (霸天虎 / 飞虎队)
Class: Scout (scou)

1. Base Body & Vehicle Mode:
   - Cloned from Sideswipe (sideswipe_gs.assetbundle)
2. Combat Animation & Moveset Grafting:
   - Normal attacks (Light 1..4, Medium 1..2): Sideswipe (Preserved)
   - Heavy Attack: Sideswipe (Preserved)
   - S1: Movie Bumblebee (bumble_bee_attackSpecial_01 / move_bumblebee_special_01)
   - S2: Starscream (starscream_gs_attackSpecial_02_stomp / move_starscream_special_02)
   - S3: Sideswipe (sideswipe_attackSpecial_03 / move_sideswipe_special_03 Preserved)
3. Visuals & Recolor:
   - Off-white body & armor, deep metallic teal-blue limbs & car flanks
   - Countach hood with orange-red trapezoid and centered purple Decepticon insignia
   - Deep metallic teal-blue helmet with vibrant orange-red faceplate and ruby glowing optics
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


def generate_breakdown_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
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
    sideswipe_bytes = load_bundle("sideswipe_gs_odr/sideswipe_gs.assetbundle")
    procedural_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")
    thundercracker_bytes = load_bundle("thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle")

    print("[*] Parsing source bundles...")
    s_env = UnityPy.load(sideswipe_bytes)
    proc_env = UnityPy.load(procedural_bytes)
    tc_env = UnityPy.load(thundercracker_bytes)

    # 1. Extract required AnimationClips
    print("[*] Extracting external animation clips...")

    # Movie Bumblebee S1: bumble_bee_attackSpecial_01 (-5764875969571546881) in procedural
    clip_s1 = None
    for obj in proc_env.objects:
        if obj.path_id == -5764875969571546881 and obj.type.name == "AnimationClip":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "breakdown_GS_attackSpecial_01"
            break

    if clip_s1 is None:
        raise ValueError("Could not find Movie Bumblebee S1 clip in character_anim_procedural.assetbundle!")

    # Starscream S2: starscream_gs_attackSpecial_02_stomp (6867043127549743747) in thundercracker
    clip_s2 = None
    for obj in tc_env.objects:
        if obj.path_id == 6867043127549743747 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "breakdown_GS_attackSpecial_02"
            break

    if clip_s2 is None:
        raise ValueError("Could not find Starscream S2 clip in thundercracker_gs_leader2015.assetbundle!")

    print("[+] Extracted Movie Bumblebee S1 and Starscream S2 animation clips!")

    # 2. Re-wire Sideswipe bundle
    print("[*] Grafting Breakdown into Sideswipe physical rig...")
    bf = list(s_env.files.values())[0]
    s_asset = list(s_env.assets)[0]

    old_cab = "CAB-9dd86eb6e9760103b0006a4297bc31f7"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-breakdown2016gs00001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    PID_S1 = 991001
    PID_S2 = 991002

    new_clips = [
        (PID_S1, clip_s1),
        (PID_S2, clip_s2),
    ]

    template_clip = [o for o in s_asset.objects.values() if o.type.name == "AnimationClip"][0]

    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab)
        new_obj.save_typetree(ctree)
        s_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} new AnimationClips into Breakdown asset!")

    # Update objects in Sideswipe bundle
    user_main_path = out_dir / "cha_breakdown_gs_main_a.png"
    user_misc_path = out_dir / "cha_breakdown_gs_tform_misc_a.png"
    user_wpns_path = out_dir / "cha_breakdown_gs_wpns_a.png"

    for obj in s_env.objects:
        # Fight AOC: override_Sideswipe_GS_fight (PathID=6324095378042686150)
        if obj.path_id == 6324095378042686150 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])

            # Slot 4: S1 -> Movie Bumblebee S1
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
            # Slot 5: S2 -> Starscream S2 Stomp
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            # Slot 31: S3 -> Preserved original Sideswipe S3

            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Breakdown Fight AOC (S1=Movie Bumblebee, S2=Starscream Stomp, S3=Sideswipe, Normals=Sideswipe)!")

        # MoveSet: PathID=-7374307588374362381
        elif obj.path_id == -7374307588374362381 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])

            # [6] S1: move_bumblebee_special_01
            moves[6]["_name"] = "move_bumblebee_special_01"
            moves[6]["_asset"] = {"m_FileID": 3, "m_PathID": -2438169768979208740}

            # [7] S2: move_starscream_special_02
            moves[7]["_name"] = "move_starscream_special_02"
            moves[7]["_asset"] = {"m_FileID": 3, "m_PathID": -4550375753452909921}

            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Breakdown MoveSet (moves[6]=Movie Bumblebee S1, moves[7]=Starscream S2)!")

        # Texture2D: Load custom recolored textures
        elif obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_sideswipe_gs_deluxe2008_main_a" and user_main_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_main_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Breakdown main texture: {user_main_path}")
            elif tex_name == "tform_misc_A" and user_misc_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_misc_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Breakdown vehicle misc texture: {user_misc_path}")
            elif tex_name == "cha_sideswipe_gs_deluxe2008_wpns_a" and user_wpns_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_wpns_path).convert("RGBA")
                tex.save()
                print(f"[+] Loaded custom Breakdown weapons texture: {user_wpns_path}")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        # AssetBundle container & preload table
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/breakdown_gs_odr/breakdown_gs.assetbundle"
            container = tree.get("m_Container", [])
            new_container = []
            for item in container:
                path_str = item[0].replace("sideswipe_gs", "breakdown_gs")
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
        elif obj.path_id in [2229594621158345595, -5937484203163368297] and obj.type.name == "GameObject":
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

    target_bundle = out_dir / "breakdown_gs.assetbundle"
    target_bundle.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")
    print("[+] Breakdown assetbundle generation complete!")


def main():
    parser = argparse.ArgumentParser(description="Generate Breakdown (打击) composite assets.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_breakdown_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
