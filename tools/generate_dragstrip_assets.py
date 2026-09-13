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
import struct
import numpy as np
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

        # For stream-backed or linked assets, update the CAB archive path
        elif obj.type.name in ["Mesh", "Texture2D", "AudioClip"]:
            tree = obj.read_typetree()
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # Texture compositing:
        # 1. Recolor Mirage main body from Blue to Dragstrip Yellow
        # 2. Recolor Mirage head helmet from Blue to Dragstrip Red (with clean silver faceplate & glowing ruby red optic)
        # 3. Recolor weapons from gray to Decepticon Purple
        from PIL import ImageDraw

        # A. Recolor and blend main_a
        user_main_path = out_dir / "cha_dragstrip_gs_deluxe2016_main_a.png"
        for obj in m_env.objects:
            if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "cha_mirage_gs_deluxe2016_main_a":
                tex = obj.read()
                if user_main_path.is_file():
                    print(f"[*] Using existing custom Dragstrip main texture: {user_main_path}")
                    tex.image = Image.open(user_main_path).convert("RGBA")
                    tex.save()
                    break

                m_img = tex.image.convert("RGBA")
                m_arr = np.array(m_img).astype(np.float32)

                r = m_arr[:, :, 0] / 255.0
                g = m_arr[:, :, 1] / 255.0
                b = m_arr[:, :, 2] / 255.0
                mx = np.maximum(np.maximum(r, g), b)
                mn = np.minimum(np.minimum(r, g), b)
                df = mx - mn

                sat = np.zeros_like(mx)
                nz = mx > 1e-5
                sat[nz] = df[nz] / mx[nz]

                hue = np.zeros_like(mx)
                mr = (mx == r) & (df > 1e-5)
                mg = (mx == g) & (df > 1e-5)
                mb = (mx == b) & (df > 1e-5)
                hue[mr] = (60.0 * ((g[mr] - b[mr]) / df[mr]) + 360.0) % 360.0
                hue[mg] = (60.0 * ((b[mg] - r[mg]) / df[mg]) + 120.0) % 360.0
                hue[mb] = (60.0 * ((r[mb] - g[mb]) / df[mb]) + 240.0) % 360.0

                # 1. Blue paint mask: captures all blue body parts & reflections
                blue_mask = (hue >= 160.0) & (hue <= 275.0) & (sat > 0.10) & (mx > 0.10)

                # 2. White / light armor mask: captures all white body panels (excluding dark mechanical frame)
                # Keep faction insignia (red) if present
                is_red_insignia = ((hue < 25.0) | (hue > 335.0)) & (sat > 0.25) & (mx > 0.5)
                white_mask = (sat < 0.25) & (mx >= 0.42) & (~is_red_insignia)

                yellow_mask = blue_mask | white_mask

                # Mirage Head: Recolor helmet from Blue to Dragstrip Red (Hue = 356 deg) & optics to glowing ruby red
                head_box = np.zeros_like(mx, dtype=bool)
                head_box[:300, :510] = True

                optics_box = np.zeros_like(mx, dtype=bool)
                optics_box[20:65, 80:135] = True
                optics_mask = (hue >= 170.0) & (hue <= 220.0) & (sat > 0.45) & (mx > 0.45) & optics_box

                helmet_blue = head_box & blue_mask & (~optics_mask)

                # Red helmet target (Hue = 356 deg)
                th = 356.0 / 360.0
                ts = np.clip(np.maximum(sat * 1.2, 0.85), 0.0, 1.0)
                tv = np.clip(mx * 0.95, 0.0, 1.0)
                rc = tv * ts
                rx = rc * (1.0 - np.abs((th * 6.0) % 2.0 - 1.0))
                rm = tv - rc
                red_r = np.clip((rc + rm) * 255.0, 0, 255).astype(np.uint8)
                red_g = np.clip((rx + rm) * 255.0, 0, 255).astype(np.uint8)
                red_b = np.clip(rm * 255.0, 0, 255).astype(np.uint8)

                # Exclude head area from yellow body paint
                yellow_mask = yellow_mask & (~head_box)

                # Target Dragstrip Warm Canary Yellow (Hue = 44 deg)
                target_h = 44.0 / 360.0
                target_s = np.where(blue_mask, np.clip(np.maximum(sat * 1.15, 0.88), 0.0, 1.0), 0.88)
                target_v = np.clip(mx * 0.96, 0.0, 1.0)

                c = target_v * target_s
                x_val = c * (1.0 - np.abs((target_h * 6.0) % 2.0 - 1.0))
                m_val = target_v - c

                new_r = np.clip((c + m_val) * 255.0, 0, 255)
                new_g = np.clip((x_val + m_val) * 255.0, 0, 255)
                new_b = np.clip((m_val) * 255.0, 0, 255)

                res_arr = np.array(m_img).copy()
                res_arr[yellow_mask, 0] = new_r[yellow_mask].astype(np.uint8)
                res_arr[yellow_mask, 1] = new_g[yellow_mask].astype(np.uint8)
                res_arr[yellow_mask, 2] = new_b[yellow_mask].astype(np.uint8)

                # Apply red helmet and ruby red optics
                res_arr[helmet_blue, 0] = red_r[helmet_blue]
                res_arr[helmet_blue, 1] = red_g[helmet_blue]
                res_arr[helmet_blue, 2] = red_b[helmet_blue]

                res_arr[optics_mask, 0] = 255
                res_arr[optics_mask, 1] = 20
                res_arr[optics_mask, 2] = 30
                print("[+] Applied Mirage red-helmet head (Metallic Red Helmet, Ruby Red Optics, Silver Face)!")

                tex.image = Image.fromarray(res_arr)
                tex.save()
                print(f"[+] Converted {np.sum(yellow_mask)} body pixels to Dragstrip Yellow on main_a!")
                break

        # B. Recolor and Blend onto tform_misc_A (back, feet, spoiler, misc chassis)
        user_misc_path = out_dir / "cha_dragstrip_gs_deluxe2016_tform_misc_a.png"
        for obj in m_env.objects:
            if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "tform_misc_A":
                tex = obj.read()
                if user_misc_path.is_file():
                    print(f"[*] Using existing custom Dragstrip vehicle texture: {user_misc_path}")
                    tex.image = Image.open(user_misc_path).convert("RGBA")
                    tex.save()
                    break

                misc_img = tex.image.convert("RGBA")
                misc_arr = np.array(misc_img).astype(np.float32)

                mr = misc_arr[:, :, 0] / 255.0
                mg = misc_arr[:, :, 1] / 255.0
                mb = misc_arr[:, :, 2] / 255.0
                mmx = np.maximum(np.maximum(mr, mg), mb)
                mmn = np.minimum(np.minimum(mr, mg), mb)
                mdf = mmx - mmn

                msat = np.zeros_like(mmx)
                mnz = mmx > 1e-5
                msat[mnz] = mdf[mnz] / mmx[mnz]

                mhue = np.zeros_like(mmx)
                mmr = (mmx == mr) & (mdf > 1e-5)
                mmg = (mmx == mg) & (mdf > 1e-5)
                mmb = (mmx == mb) & (mdf > 1e-5)
                mhue[mmr] = (60.0 * ((mg[mmr] - mb[mmr]) / mdf[mmr]) + 360.0) % 360.0
                mhue[mmg] = (60.0 * ((mb[mmg] - mr[mmg]) / mdf[mmg]) + 120.0) % 360.0
                mhue[mmb] = (60.0 * ((mr[mmb] - mg[mmb]) / mdf[mmb]) + 240.0) % 360.0

                # All blue pixels in tform_misc_A (back, soles/feet, chassis)
                misc_blue_mask = (mhue >= 160.0) & (mhue <= 275.0) & (msat > 0.08) & (mmx > 0.10)

                # All white/light armor panels (back, rear wing, body panels)
                # Keep red insignia if present
                is_red_insignia = ((mhue < 25.0) | (mhue > 335.0)) & (msat > 0.25) & (mmx > 0.5)
                misc_white_mask = (msat < 0.25) & (mmx >= 0.42) & (~is_red_insignia)

                misc_yellow_mask = misc_blue_mask | misc_white_mask
                target_h = 44.0 / 360.0
                target_s = np.where(misc_blue_mask, np.clip(np.maximum(msat * 1.15, 0.88), 0.0, 1.0), 0.88)
                target_v = np.clip(mmx * 0.96, 0.0, 1.0)

                c = target_v * target_s
                x_val = c * (1.0 - np.abs((target_h * 6.0) % 2.0 - 1.0))
                m_val = target_v - c

                new_r = np.clip((c + m_val) * 255.0, 0, 255)
                new_g = np.clip((x_val + m_val) * 255.0, 0, 255)
                new_b = np.clip((m_val) * 255.0, 0, 255)

                res_misc = np.array(misc_img).copy()
                res_misc[misc_yellow_mask, 0] = new_r[misc_yellow_mask].astype(np.uint8)
                res_misc[misc_yellow_mask, 1] = new_g[misc_yellow_mask].astype(np.uint8)
                res_misc[misc_yellow_mask, 2] = new_b[misc_yellow_mask].astype(np.uint8)

                tex.image = Image.fromarray(res_misc)
                tex.save()
                print(f"[+] Converted {np.sum(misc_yellow_mask)} pixels (back, feet, white panels) to Dragstrip Yellow on tform_misc_A!")
                break

        # C. Recolor weapons (cha_mirage_gs_deluxe2016_wpns_a) to Decepticon Purple
        user_wpns_path = out_dir / "cha_dragstrip_gs_deluxe2016_wpns_a.png"
        for obj in m_env.objects:
            if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "cha_mirage_gs_deluxe2016_wpns_a":
                tex = obj.read()
                if user_wpns_path.is_file():
                    print(f"[*] Using existing custom Dragstrip weapons texture: {user_wpns_path}")
                    tex.image = Image.open(user_wpns_path).convert("RGBA")
                    tex.save()
                    break

                w_img = tex.image.convert("RGBA")
                w_arr = np.array(w_img).astype(np.float32)
                # Compute luminance
                w_gray = (0.299 * w_arr[:, :, 0] + 0.587 * w_arr[:, :, 1] + 0.114 * w_arr[:, :, 2]) / 255.0
                # Decepticon weapon purple tint (R: 95, G: 45, B: 155)
                purp_r = np.clip(w_gray * 95, 0, 255).astype(np.uint8)
                purp_g = np.clip(w_gray * 45, 0, 255).astype(np.uint8)
                purp_b = np.clip(w_gray * 155, 0, 255).astype(np.uint8)

                out_w = np.array(w_img).copy()
                out_w[:, :, 0] = purp_r
                out_w[:, :, 1] = purp_g
                out_w[:, :, 2] = purp_b
                tex.image = Image.fromarray(out_w)
                tex.save()
                print("[+] Recolored Dragstrip blasters to Decepticon Purple!")
                break

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
