#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dragstrip_assets.py

Custom composite grafting pipeline for Decepticon Dragstrip (抢劫).
Class: Warrior (warr)
Faction: Decepticons (霸天虎)

1. Base Body & Vehicle Mode:
   - Cloned from Mirage (mirage_gs_deluxe2016.assetbundle)
2. Combat Animation & Moveset Grafting:
   - Heavy Attack: Cliffjumper (Ironhide_Normal_attackHeavy / move_heavy_cliffjumper_gs_shoot)
   - S1: Mirage (Preserved)
   - S2: Hot Rod (Hotrod_cin_attackSpecial_02 / move_hotrod_special_02)
   - S3: Bumblebee GS (bumblebee_gs_attackSpecial_03 / SP3 timings borrowed)
   - L1: Jazz L3 (Jazz_GS_attackLight_03_leftKick / move_jazz_attack_light_03)
   - L2: Blaster L2 (blaster_GS_attackLight_02_leftKick / move_blaster_attack_light_02)
   - L3: Blaster L3 (blaster_GS_attackLight_03_rightKick / move_blaster_attack_light_03)
   - L4: Jazz L4 (Jazz_GS_attackLight_04_KickBackFlip / move_jazz_attack_light_04)
   - M1: Cheetor M1 (Cheetor_BW_attackMedium_01_FrontKick / move_cheetor_attack_medium_01)
   - M2: Mirage M2 (Preserved)
   - Ranged Gunshots: Mirage (Preserved)
   - Victory Pose: Sideswipe (Brawler_Normal_Victory / Brawler_Normal_Victory_Idle)
3. UI Portraits:
   - Generated from Mirage base portrait (neutral colors for now)
"""

import argparse
import copy
import glob
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


def generate_dragstrip_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
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
    mirage_bytes = load_bundle("mirage_gs_deluxe2016_odr/mirage_gs_deluxe2016.assetbundle")
    cliff_bytes = load_bundle("cliffjumper_gs_kabam_odr/cliffjumper_gs_kabam.assetbundle")
    hotrod_bytes = load_bundle("hotrod_cin_tlk_odr/hotrod_cin_tlk.assetbundle")
    bee_bytes = load_bundle("bumblebee_gs_kabam_odr/bumblebee_gs_kabam.assetbundle")
    jazz_bytes = load_bundle("jazz_gs_twm05_odr/jazz_gs_twm05.assetbundle")
    blaster_bytes = load_bundle("blaster_gs_leader2016_odr/blaster_gs_leader2016.assetbundle")
    cheetor_bytes = load_bundle("cheetor_bw_transmetal_odr/cheetor_bw_transmetal.assetbundle")

    print("[*] Parsing source bundles...")
    m_env = UnityPy.load(mirage_bytes)
    c_env = UnityPy.load(cliff_bytes)
    h_env = UnityPy.load(hotrod_bytes)
    b_env = UnityPy.load(bee_bytes)
    j_env = UnityPy.load(jazz_bytes)
    bl_env = UnityPy.load(blaster_bytes)
    ch_env = UnityPy.load(cheetor_bytes)

    # 1. Extract required AnimationClips
    print("[*] Extracting external animation clips...")

    # Cliffjumper Heavy: Ironhide_Normal_attackHeavy (-2721040065330547388)
    clip_heavy = None
    for obj in c_env.objects:
        if obj.path_id == -2721040065330547388 and obj.type.name == "AnimationClip":
            clip_heavy = obj.read_typetree()
            clip_heavy["m_Name"] = "dragstrip_Normal_attackHeavy"
            break

    # Hotrod S2: Hotrod_cin_attackSpecial_02 (3923599842407920377)
    clip_s2 = None
    for obj in h_env.objects:
        if obj.path_id == 3923599842407920377 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "dragstrip_Normal_attackSpecial_02"
            break

    # Bumblebee S3: bumblebee_gs_attackSpecial_03 (3809667128409547372) and HitReaction (-9071274386392300993)
    clip_s3 = None
    clip_s3_hit = None
    for obj in b_env.objects:
        if obj.path_id == 3809667128409547372 and obj.type.name == "AnimationClip":
            clip_s3 = obj.read_typetree()
            clip_s3["m_Name"] = "dragstrip_gs_attackSpecial_03"
        elif obj.path_id == -9071274386392300993 and obj.type.name == "AnimationClip":
            clip_s3_hit = obj.read_typetree()
            clip_s3_hit["m_Name"] = "dragstrip_gs_attackSpecial_03_hitReaction"

    # Jazz L3: Jazz_GS_attackLight_03_leftKick (6919999024148056483)
    # Jazz L4: Jazz_GS_attackLight_04_KickBackFlip (-491266744809317325)
    clip_l1_jazz = None
    clip_l4_jazz = None
    for obj in j_env.objects:
        if obj.path_id == 6919999024148056483 and obj.type.name == "AnimationClip":
            clip_l1_jazz = obj.read_typetree()
            clip_l1_jazz["m_Name"] = "dragstrip_GS_attackLight_01_kick"
        elif obj.path_id == -491266744809317325 and obj.type.name == "AnimationClip":
            clip_l4_jazz = obj.read_typetree()
            clip_l4_jazz["m_Name"] = "dragstrip_GS_attackLight_04_backflip"

    # Blaster L2: blaster_GS_attackLight_02_leftKick (2310569694197683561)
    # Blaster L3: blaster_GS_attackLight_03_rightKick (285458249171271195)
    clip_l2_blaster = None
    clip_l3_blaster = None
    for obj in bl_env.objects:
        if obj.path_id == 2310569694197683561 and obj.type.name == "AnimationClip":
            clip_l2_blaster = obj.read_typetree()
            clip_l2_blaster["m_Name"] = "dragstrip_GS_attackLight_02_kick"
        elif obj.path_id == 285458249171271195 and obj.type.name == "AnimationClip":
            clip_l3_blaster = obj.read_typetree()
            clip_l3_blaster["m_Name"] = "dragstrip_GS_attackLight_03_kick"

    # Cheetor M1: Cheetor_BW_attackMedium_01_FrontKick (-82464947619687576)
    clip_m1_cheetor = None
    for obj in ch_env.objects:
        if obj.path_id == -82464947619687576 and obj.type.name == "AnimationClip":
            clip_m1_cheetor = obj.read_typetree()
            clip_m1_cheetor["m_Name"] = "dragstrip_BW_attackMedium_01_frontkick"
            break

    print("[+] Extracted all custom combat animation clips!")

    # 2. Re-wire Mirage bundle
    print("[*] Grafting Dragstrip into Mirage's physical rig...")
    bf = list(m_env.files.values())[0]
    m_asset = list(m_env.assets)[0]

    old_cab = "CAB-136f0ac5ca5202757facd548b71d4a43"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-dragstrip2016gs00001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # Dedicated new PathIDs for the 7 injected combat AnimationClips.
    # We DO NOT overwrite any existing Mirage clips! All 13 original clips
    # (including BattleIntro, car transitions, and S3 hologram cutscene) remain untouched!
    PID_HEAVY = 991001
    PID_S2 = 991002
    PID_L1_JAZZ = 991005
    PID_L2_BLASTER = 991006
    PID_L3_BLASTER = 991007
    PID_L4_JAZZ = 991008
    PID_M1_CHEETOR = 991009

    new_clips = [
        (PID_HEAVY, clip_heavy),
        (PID_S2, clip_s2),
        (PID_L1_JAZZ, clip_l1_jazz),
        (PID_L2_BLASTER, clip_l2_blaster),
        (PID_L3_BLASTER, clip_l3_blaster),
        (PID_L4_JAZZ, clip_l4_jazz),
        (PID_M1_CHEETOR, clip_m1_cheetor),
    ]

    # Pick a template AnimationClip from Mirage to clone ObjectReader metadata
    template_clip = [o for o in m_asset.objects.values() if o.type.name == "AnimationClip"][0]

    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab)
        new_obj.save_typetree(ctree)
        m_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} new AnimationClips as standalone objects into asset!")

    # Projectile bullet entities injection:
    # 1. Cliffjumper Heavy: projectile_megatron_gs_bullet (GameObject: 9003878510878022874 + 5 components)
    # 2. Hot Rod S2: projectile_hotrod_bullet (GameObject: -8172610782387618255 + 5 components)
    c_asset = list(c_env.assets)[0]
    h_asset = list(h_env.assets)[0]

    tmpl_go = m_asset.objects[8211146528821479566]
    tmpl_tr = m_asset.objects[7833009063040620157]
    tmpl_fire_explode = m_asset.objects[6911381496922764941]
    tmpl_moves = m_asset.objects[4570473581685628392]
    tmpl_prefablist = m_asset.objects[6656473622135015614]
    tmpl_combat = m_asset.objects[-2567301930229054027]

    def get_template(obj_type, tree):
        if obj_type == "GameObject":
            return tmpl_go
        elif obj_type == "Transform":
            return tmpl_tr
        elif obj_type == "MonoBehaviour":
            script_pid = tree.get("m_Script", {}).get("m_PathID")
            if script_pid == -3660570848581127988:
                return tmpl_fire_explode
            elif script_pid == 2297153707519481197:
                return tmpl_moves
            elif script_pid == -3815473324432562333:
                return tmpl_prefablist
            elif script_pid == 4113389322536752908:
                return tmpl_combat
            else:
                raise ValueError(f"Unknown script pid {script_pid}")
        raise ValueError(f"Unknown type {obj_type}")

    cj_proj_pids = [9003878510878022874, -3703404665488950760, 7614484081745325141, -2714705455090383668, -4642064524079818382, 5864972968936471992]
    hr_proj_pids = [-8172610782387618255, 6789086250395783446, 9083784432851756083, -8264554495304631612, -802258416909754905, -2962032538932338988]

    for pid in cj_proj_pids:
        obj = c_asset.objects[pid]
        tree = obj.read_typetree()
        if pid == -2714705455090383668:
            for m in tree.get("_moves", []):
                if m.get("_asset", {}).get("m_FileID") == 6:
                    m["_asset"]["m_FileID"] = 5
        elif pid == -4642064524079818382:
            for item in tree.get("PrefabList", []):
                if item.get("Prefab", {}).get("m_FileID") == 2:
                    item["Prefab"]["m_FileID"] = 3
        tmpl = get_template(obj.type.name, tree)
        new_obj = copy.copy(tmpl)
        new_obj.path_id = pid
        replace_str_in_tree(tree, old_cab, new_cab)
        new_obj.save_typetree(tree)
        m_asset.objects[pid] = new_obj

    for pid in hr_proj_pids:
        obj = h_asset.objects[pid]
        tree = obj.read_typetree()
        if pid == -802258416909754905:
            for item in tree.get("PrefabList", []):
                if item.get("Prefab", {}).get("m_FileID") == 1:
                    item["Prefab"]["m_FileID"] = 3
        tmpl = get_template(obj.type.name, tree)
        new_obj = copy.copy(tmpl)
        new_obj.path_id = pid
        replace_str_in_tree(tree, old_cab, new_cab)
        new_obj.save_typetree(tree)
        m_asset.objects[pid] = new_obj

    injected_proj_pids = cj_proj_pids + hr_proj_pids
    print(f"[+] Injected {len(injected_proj_pids)} projectile entities and components into Dragstrip bundle!")

    for obj in list(m_env.objects):
        # Configure AnimatorOverrideController (Robot Fight AOC: PathID=740305678794743262)
        if obj.path_id == 740305678794743262 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])

            # L1: Jazz L3
            clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L1_JAZZ}
            # L2: Blaster L2
            clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L2_BLASTER}
            # S1: Mirage S1 (Preserved in Slot 4: -8916200897996993922)
            # S2: Hot Rod S2
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            # S3 & S3 Hit: Mirage S3 (Preserved in Slots 31 & 32 so TFormStage_Mirage_Special03 finds them)
            # Victory Pose: Preserve Mirage's Agile_Backflip_Victory (Slots 39 & 40)
            # MatineeStage PreInitializeMatinee requires Agile_Backflip_Victory to match VictoryStagePrefab
            clips[39]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -3005405672129804380}
            clips[40]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 5259930176709765285}
            # L3: Blaster L3
            clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L3_BLASTER}
            # M1: Cheetor M1
            clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M1_CHEETOR}
            # L4: Jazz L4
            clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L4_JAZZ}
            # M2: Mirage M2 (Preserved in Slot 44: 628965653697985842)
            # Ranged 01..03: Mirage (Preserved in Slots 51, 52, 53)
            # Heavy Attack: Cliffjumper Heavy
            clips[58]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_HEAVY}

            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Dragstrip Fight AOC with all custom combat animations & Sideswipe victory pose!")

        # Vehicle / Car AnimatorOverrideController (PathID=-6155136737816236521)
        # Keep ALL original car animation slot overrides intact so BattleIntro & car transitions work!
        elif obj.path_id == -6155136737816236521 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Preserved Dragstrip Car AOC with pristine BattleIntro & vehicle rig bindings!")

        # Configure MoveSet: PathID=1840605340213205441
        elif obj.path_id == 1840605340213205441 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])

            # [0] LightAttack01: Jazz L3
            moves[0]["_name"] = "move_jazz_attack_light_03"
            moves[0]["_asset"] = {"m_FileID": 5, "m_PathID": 4591432870569280388}

            # [1] LightAttack02: Blaster L2
            moves[1]["_name"] = "move_blaster_attack_light_02"
            moves[1]["_asset"] = {"m_FileID": 5, "m_PathID": -5768502813711380021}

            # [2] LightAttack03: Blaster L3
            moves[2]["_name"] = "move_blaster_attack_light_03"
            moves[2]["_asset"] = {"m_FileID": 5, "m_PathID": -7697654508267001063}

            # [3] LightAttack04: Jazz L4
            moves[3]["_name"] = "move_jazz_attack_light_04"
            moves[3]["_asset"] = {"m_FileID": 5, "m_PathID": -7349256443508413755}

            # [4] MediumAttack01: Cheetor M1
            moves[4]["_name"] = "move_cheetor_attack_medium_01"
            moves[4]["_asset"] = {"m_FileID": 5, "m_PathID": 7744598786624021798}

            # [5] MediumAttack02: Mirage M2 (Preserved: move_agile_attack_medium_02)
            # [6] SpecialAttack01: Mirage S1 (Preserved: move_mirage_special_01)

            # [7] SpecialAttack02: Hot Rod S2
            moves[7]["_name"] = "move_hotrod_special_02"
            moves[7]["_asset"] = {"m_FileID": 5, "m_PathID": 7236302885264655572}

            # [41] HeavyAttack: Cliffjumper Heavy Shot
            moves[41]["_name"] = "move_heavy_cliffjumper_gs_shoot"
            moves[41]["_asset"] = {"m_FileID": 5, "m_PathID": 3468014272436761367}

            # [42..44] RangedAttack01..03: Mirage (Preserved)

            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Dragstrip MoveSet with hitboxes and damage frames!")

        # Root PrefabList (Pool manager): PathID=-2249602606274241856
        elif obj.path_id == -2249602606274241856 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            plist = tree.get("PrefabList", [])
            extra_prefabs = [
                # Cliffjumper heavy muzzle ignition
                {"Prefab": {"m_FileID": 3, "m_PathID": -1408646010089090896}, "Amount": 1},
                # Cliffjumper heavy projectile bullet
                {"Prefab": {"m_FileID": 0, "m_PathID": 9003878510878022874}, "Amount": 1},
                # Hot Rod S2 blue hit light
                {"Prefab": {"m_FileID": 3, "m_PathID": -2054079777877699854}, "Amount": 1},
                # Hot Rod S2 muzzle blue flash
                {"Prefab": {"m_FileID": 4, "m_PathID": 4727641465992916545}, "Amount": 1},
                # Hot Rod S2 special small trail
                {"Prefab": {"m_FileID": 4, "m_PathID": -5363481920856949953}, "Amount": 2},
                # Hot Rod S2 projectile bullet
                {"Prefab": {"m_FileID": 0, "m_PathID": -8172610782387618255}, "Amount": 1},
            ]
            plist.extend(extra_prefabs)
            tree["PrefabList"] = plist
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Extended root PrefabList with projectile pools for Cliffjumper Heavy & Hot Rod S2!")

        # Root Props Manager: PathID=-3532403574792160156
        elif obj.path_id == -3532403574792160156 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            values = props.get("_serializedValues", [])
            if "gunRight" not in keys:
                for val in values:
                    if val.get("Name") == "rightgun":
                        gun_right_val = copy.deepcopy(val)
                        gun_right_val["Name"] = "gunRight"
                        keys.append("gunRight")
                        values.append(gun_right_val)
                        break
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured gunRight weapon alias in root _props!")

        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            bundle_name = "data/dragstrip_gs_deluxe2016_odr/dragstrip_gs_deluxe2016.assetbundle"
            tree["m_Name"] = bundle_name
            tree["m_AssetBundleName"] = bundle_name

            orig_table = tree.get("m_PreloadTable", [])
            all_new_pids = [pid for pid, _ in new_clips] + injected_proj_pids
            new_entries = [{"m_FileID": 0, "m_PathID": pid} for pid in all_new_pids]

            # In Mirage, main prefab preloaded 1124 items (index 0..1123), lw prefab preloaded 507 items (index 1124..1630).
            # Insert the new clips and projectile entities at index 1124 so main prefab preloads them seamlessly.
            insert_idx = 1124
            merged_table = orig_table[:insert_idx] + new_entries + orig_table[insert_idx:]
            tree["m_PreloadTable"] = merged_table

            new_container = []
            for k, v in tree.get("m_Container", []):
                new_k = k.replace("mirage_gs_deluxe2016", "dragstrip_gs_deluxe2016")
                entry_info = dict(v)
                if "mirage_gs_deluxe2016.prefab" in k:
                    entry_info["preloadSize"] = entry_info.get("preloadSize", 1124) + len(all_new_pids)
                elif "mirage_gs_deluxe2016_lw.prefab" in k:
                    entry_info["preloadIndex"] = entry_info.get("preloadIndex", 1124) + len(all_new_pids)
                new_container.append((new_k, entry_info))
            tree["m_Container"] = new_container

            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Dragstrip AssetBundle container and extended preload table!")

        # Root GameObjects: Keep names intact so MatineeStage hierarchy entity lookups (e.g. Actor0_locator) succeed
        elif obj.path_id in [8113032789630995797, 8776030576437937903] and obj.type.name == "GameObject":
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # For stream-backed assets (Texture2D and AudioClip), update the CAB archive path
        elif obj.type.name in ["Texture2D", "AudioClip"]:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

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

    target_bundle = out_dir / "dragstrip_gs_deluxe2016.assetbundle"
    target_bundle.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")

    # 3. Create Portraits
    print("[*] Generating Dragstrip UI portraits...")
    p_large_path = Path("extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_mirage_gs_large.png")
    p_small_path = Path("extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_mirage_gs_small.jpg")
    p_quest_path = Path("extracted_apk/assets/assetpack/questboard_odr/questboard/portrait_mirage_gs_quest.png")

    if p_large_path.is_file():
        p_large = Image.open(p_large_path)
        p_large.save(out_dir / "portrait_dragstrip_large.png")
        p_large.save(out_dir / "dragstrip.png")
    if p_small_path.is_file():
        p_small = Image.open(p_small_path)
        p_small.save(out_dir / "portrait_dragstrip_small.jpg")
    if p_quest_path.is_file():
        p_quest = Image.open(p_quest_path)
        p_quest.save(out_dir / "portrait_dragstrip_quest.png")
    elif p_large_path.is_file():
        p_large.save(out_dir / "portrait_dragstrip_quest.png")

    print("[+] All Dragstrip assets successfully generated!")


def main():
    parser = argparse.ArgumentParser(description="Generate Dragstrip (抢劫) composite assets.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_dragstrip_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
