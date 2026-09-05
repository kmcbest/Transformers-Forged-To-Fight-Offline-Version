#!/usr/bin/env python3
"""
generate_starsaber_assets.py

Complete composite grafting pipeline for Autobot Supreme Commander Star Saber (史达).
Performs:
1. Physical 3D Mesh & Hierarchy grafting:
   - Replaces Jetfire's rifle mesh with Motormaster's Saber Blade
   - Renames weapon GameObjects ('gun' -> 'sword', 'cha_jetfire_gs_leader2014_wpns_rifle_right' -> 'cha_starsaber_gs_leader2014_wpns_sword')
   - Enables weapon SkinnedMeshRenderer (m_Enabled = True) so sword is permanently held and visible
2. Combat Animation State Machine (FileID = 2 procedural rig):
   - Slots [2, 3, 41, 43, 42, 44]: Motormaster / Swordsman Light & Medium Attack Combos
   - Slot [4]: Swordsman S1 (drift_cin_attackSpecial_01 - 破空拔刀斩)
   - Slot [5]: Swordsman S2 (drift_cin_attackSpecial_02 - 旋风剑舞)
   - Slot [58]: Windblade Heavy Attack (windblade_Normal_attackHeavy - 风刃重击)
   - Slots [51, 52, 53]: Jetfire Original Ranged Shooting (Preserved!)
   - Slot [31]: Jetfire S3 Supersonic Air Raid (Preserved!)
3. MoveSet MoveInfo rewiring for hitboxes and damage frames
4. Procedural Victory color synthesis (Ceramic White, Victory Red, Cobalt Blue, Imperial Gold)
5. Deep CAB & namespace isolation (CAB-7e3f890123456789abcdef0123456789)

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


def generate_starsaber_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_dir = Path("extracted_apk")
    if (extracted_dir / "assets/assetpack").is_dir():
        print("[*] Loading base components directly from extracted_apk/ ...")
        j_bundle_data = (extracted_dir / "assets/assetpack/jetfire_gs_leader2014_odr/jetfire_gs_leader2014.assetbundle").read_bytes()
        m_bundle_data = (extracted_dir / "assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle").read_bytes()
        w_bundle_data = (extracted_dir / "assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle").read_bytes()
        p_large_bytes = (extracted_dir / "assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_large.png").read_bytes()
        p_small_bytes = (extracted_dir / "assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_small.jpg").read_bytes()
        p_quest_bytes = p_large_bytes
    elif apk_path and Path(apk_path).is_file():
        apk_file = Path(apk_path)
        print(f"[*] Extracting base components from: {apk_file.name} ...")
        with zipfile.ZipFile(apk_file, "r") as z:
            j_bundle_data = z.read("assets/assetpack/jetfire_gs_leader2014_odr/jetfire_gs_leader2014.assetbundle")
            m_bundle_data = z.read("assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle")
            w_bundle_data = z.read("assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle")
            p_large_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_large.png")
            p_small_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_jetfire_gs_small.jpg")
            p_quest_bytes = p_large_bytes
    else:
        raise FileNotFoundError(f"Neither extracted_apk/ nor a valid APK was found: {apk_path}")


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
    m_wpns_raoe_img = None
    for obj in m_env.objects:
        if obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if "wpns_a" in tname:
                m_wpns_img = obj.read().image
            elif tname == "wpns_RAOE":
                m_wpns_raoe_img = obj.read().image

    # 1. Main Body Texture Recolor (Star Saber Victory Scheme)
    j_arr = np.array(j_main_img.convert("RGBA"), dtype=np.float32)
    jr, jg, jb, ja = j_arr[:, :, 0], j_arr[:, :, 1], j_arr[:, :, 2], j_arr[:, :, 3]
    lum = (jr * 0.299 + jg * 0.587 + jb * 0.114) / 255.0

    is_red_accents = (jr > 120) & (jg < 80) & (jb < 80)
    is_black_metals = (lum < 0.25)
    is_white_armor = (lum >= 0.25) & (~is_red_accents)

    # Star Saber Colors:
    # A. Victory Crimson Red for chest, wings, and thrusters
    ss_red_r = np.clip(lum * 180.0 + 75.0, 0, 255)
    ss_red_g = np.clip(lum * 25.0 + 5.0, 0, 255)
    ss_red_b = np.clip(lum * 35.0 + 10.0, 0, 255)

    # B. Star Saber Navy/Cobalt Blue for faceplate, shin trims, and accents
    ss_blue_r = np.clip(lum * 20.0 + 8.0, 0, 255)
    ss_blue_g = np.clip(lum * 60.0 + 25.0, 0, 255)
    ss_blue_b = np.clip(lum * 180.0 + 75.0, 0, 255)

    # C. Pure Ceramic White for main body armor
    ss_white_r = np.clip(lum * 140.0 + 115.0, 0, 255)
    ss_white_g = np.clip(lum * 140.0 + 115.0, 0, 255)
    ss_white_b = np.clip(lum * 145.0 + 115.0, 0, 255)

    # Composite Main Texture
    final_r = np.where(is_red_accents, ss_red_r, np.where(is_black_metals, ss_blue_r, ss_white_r))
    final_g = np.where(is_red_accents, ss_red_g, np.where(is_black_metals, ss_blue_g, ss_white_g))
    final_b = np.where(is_red_accents, ss_red_b, np.where(is_black_metals, ss_blue_b, ss_white_b))

    final_main_img = Image.fromarray(np.stack([final_r, final_g, final_b, ja], axis=-1).astype(np.uint8))
    final_main_img.save(out_dir / "cha_starsaber_gs_leader2014_main_a.png")

    # 2. Saber Blade Weapons Texture Synthesis
    w_arr = np.array(m_wpns_img.convert("RGBA"), dtype=np.float32)
    wr, wg, wb, wa = w_arr[:, :, 0], w_arr[:, :, 1], w_arr[:, :, 2], w_arr[:, :, 3]
    wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0

    # Saber Blade: Golden guard + blue grip + glowing energy blade
    saber_blade_r = np.clip(wlum * 180.0 + 75.0, 0, 255)
    saber_blade_g = np.clip(wlum * 195.0 + 60.0, 0, 255)
    saber_blade_b = np.clip(wlum * 240.0 + 25.0, 0, 255)

    final_wpns_img = Image.fromarray(np.stack([saber_blade_r, saber_blade_g, saber_blade_b, wa], axis=-1).astype(np.uint8))
    final_wpns_img.save(out_dir / "cha_starsaber_gs_leader2014_wpns_a.png")

    # 3. Saber Blade Emissive RAOE Texture Synthesis (Ghost/Energon Blue Shimmer)
    raoe_rgb = np.array(m_wpns_raoe_img.convert("RGB"), dtype=np.uint8)
    diffuse_small = np.array(m_wpns_img.convert("RGBA").resize(m_wpns_raoe_img.size, Image.Resampling.BILINEAR))
    diff_lum = (diffuse_small[..., 0] * 0.299 + diffuse_small[..., 1] * 0.587 + diffuse_small[..., 2] * 0.114) / 255.0
    emissive_alpha = np.clip(diff_lum * 255.0 * 1.2, 120, 255).astype(np.uint8)
    final_raoe_img = Image.fromarray(np.dstack([raoe_rgb, emissive_alpha]), "RGBA")
    print("[+] Synthesized 4-channel wpns_RAOE with high-intensity Emissive Alpha mask!")

    print("[*] Extracting Motormaster Saber Blade Mesh...")
    sword_mesh_tree = None
    for obj in m_env.objects:
        if obj.type.name == "Mesh" and "sword" in obj.read_typetree().get("m_Name", ""):
            sword_mesh_tree = obj.read_typetree()
            sword_mesh_tree["m_Name"] = "cha_starsaber_gs_leader2014_wpns_sword"
            break

    print("[*] Extracting Windblade S2 AnimationClip...")
    wb_s2_clip_tree = None
    for obj in w_env.objects:
        if obj.path_id == -2626501024704866973 and obj.type.name == "AnimationClip":
            wb_s2_clip_tree = obj.read_typetree()
            wb_s2_clip_tree["m_Name"] = "cha_starsaber_gs_leader2014_attackSpecial_02"
            print("[+] Successfully extracted Windblade S2 Cyclone Dance AnimationClip!")
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

    for obj in j_env.objects:
        if obj.path_id == -4439679313609908059 and obj.type.name == "Mesh" and sword_mesh_tree is not None:
            tree = sword_mesh_tree
            # Section 7.1 of SKILL.md: BindPose[0] set to Matrix4x4.identity
            tree["m_BindPose"] = [{'e00': 1.0, 'e01': 0.0, 'e02': 0.0, 'e03': 0.0,
                                   'e10': 0.0, 'e11': 1.0, 'e12': 0.0, 'e13': 0.0,
                                   'e20': 0.0, 'e21': 0.0, 'e22': 1.0, 'e23': 0.0,
                                   'e30': 0.0, 'e31': 0.0, 'e32': 0.0, 'e33': 1.0}]
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Saber Blade Mesh into weapon slot with identity bindpose")
        elif obj.path_id in [738325550751503188, -6612254241771744554] and obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            tree["m_Enabled"] = True
            tree["m_Mesh"] = {"m_FileID": 0, "m_PathID": -4439679313609908059}
            # Section 7.1 of SKILL.md: RightProp bone
            prop_bone_id = -738255178390998769 if obj.path_id == 738325550751503188 else -3662838891856763018
            tree["m_Bones"] = [{"m_FileID": 0, "m_PathID": prop_bone_id}]
            tree["m_RootBone"] = {"m_FileID": 0, "m_PathID": prop_bone_id}
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Rigged SkinnedMeshRenderer (PathID={obj.path_id}) to RightProp ({prop_bone_id})!")
        elif obj.path_id in [-9009354885740569570, 1062452820465670706] and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            vals = props.get("_serializedValues", [])
            for k_idx, k_name in enumerate(keys):
                if k_name in ["gun", "sword"]:
                    keys[k_idx] = "sword"
                    val = vals[k_idx]
                    val["Name"] = "sword"
                    val["InitFlags"] = 6  # Always active (Motormaster standard)
                    val["_startActive"] = True
            if "gun" not in keys:
                keys.append("gun")
                vals.append({
                    "Name": "gun",
                    "PropType": 0,
                    "InitFlags": 0,
                    "RootPath": "",
                    "PrefabAssetGUID": "",
                    "OverrideController": {"m_FileID": 0, "m_PathID": 0},
                    "PositionOffset": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "RotationOffset": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "Scale": {"x": 1.0, "y": 1.0, "z": 1.0},
                    "_instance": {"m_FileID": 0, "m_PathID": 0},
                    "_animator": {"m_FileID": 0, "m_PathID": 0},
                    "_renderers": []
                })
            props["_serializedKeys"] = keys
            props["_serializedValues"] = vals
            tree["_props"] = props
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Configured PropsController (PathID={obj.path_id}) with sword InitFlags=6 and dummy gun prop")
        elif obj.path_id == 6966345187514932495 and obj.type.name == "AnimationClip" and wb_s2_clip_tree is not None:
            tree = wb_s2_clip_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully injected Windblade S2 AnimationClip into slot 6966345187514932495!")
        elif obj.path_id == -8402565767957608701 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            # Motormaster Sword Combos:
            clips[2]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 740649405912261330}   # Light 01
            clips[3]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -2512025252598410331} # Light 02
            clips[41]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4980757935915932854} # Light 03
            clips[43]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4106831893816218441} # Light 04
            clips[42]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 6308122467145514604}  # Medium 01
            clips[44]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -705967800912522861}  # Medium 02
            clips[45]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 7146863003282264883}  # Sword Block React
            clips[46]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 7146863003282264883}  # Sword Block React Ranged
            # S1: Drift S1 (drift_cin_attackSpecial_01 - 破空拔刀斩)
            clips[4]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -3664095140934993801}  # Slot 4 = SpecialAttack01
            # S2: Windblade S2 (Windblade_normal_attackSpecial_02 - 旋风剑舞)
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 6966345187514932495}  # Slot 5 = SpecialAttack02
            # Heavy Attack: Windblade Heavy Attack (windblade_Normal_attackHeavy)
            clips[58]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 2534697979766001969} # Slot 58 = HeavyAttack
            # Ranged Shooting: Jetfire Original Ranged Shooting (Preserved!)
            clips[51]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 7808332553383168359} # Slot 51 = Ranged 01
            clips[52]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -7264490462704346615} # Slot 52 = Ranged 02
            clips[53]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -1145688102861077554} # Slot 53 = Ranged 03
            # S3: Jetfire S3 Supersonic Air Raid (Preserved!)
            clips[31]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -4700446166485423738} # Slot 31 = SpecialAttack03
            clips[32]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 5007219591915846681}  # Slot 32 = SpecialAttack03 Reaction
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully grafted AnimatorOverrideController fight clips with true procedural rig!")
        elif obj.path_id == 2601823321879744519 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            if len(moves) >= 50:
                moves[0] = {"_name": "move_sword_attack_light_01", "_animStateName": "Base.LightAttack01", "_asset": {"m_FileID": 3, "m_PathID": -1283304507747283112}}
                moves[1] = {"_name": "move_sword_attack_light_02", "_animStateName": "Base.LightAttack02", "_asset": {"m_FileID": 3, "m_PathID": 7616440351077033282}}
                moves[2] = {"_name": "move_sword_attack_light_03", "_animStateName": "Base.LightAttack03", "_asset": {"m_FileID": 3, "m_PathID": -3329254882358104680}}
                moves[3] = {"_name": "move_sword_attack_light_04", "_animStateName": "Base.LightAttack04", "_asset": {"m_FileID": 3, "m_PathID": 4145453135915101152}}
                moves[4] = {"_name": "move_sword_attack_medium_01", "_animStateName": "Base.MediumAttack01", "_asset": {"m_FileID": 3, "m_PathID": -1389778547757567769}}
                moves[5] = {"_name": "move_sword_attack_medium_02", "_animStateName": "Base.MediumAttack02", "_asset": {"m_FileID": 3, "m_PathID": -3898379380470346085}}
                moves[6] = {"_name": "move_drift_special_01", "_animStateName": "Base.SpecialAttack01", "_asset": {"m_FileID": 3, "m_PathID": -6173328959056132852}}
                moves[7] = {"_name": "move_windblade_special_02", "_animStateName": "Base.SpecialAttack02", "_asset": {"m_FileID": 3, "m_PathID": -6524404075124180520}}
                moves[8] = {"_name": "move_sword_block_react", "_animStateName": "Base.BlockReact", "_asset": {"m_FileID": 3, "m_PathID": 2656533506074151531}}
                moves[9] = {"_name": "move_sword_block_react", "_animStateName": "Base.BlockReactRanged", "_asset": {"m_FileID": 3, "m_PathID": 6843684539569461767}}
                moves[41] = {"_name": "move_heavy_plane_donut", "_animStateName": "Base.HeavyAttack", "_asset": {"m_FileID": 3, "m_PathID": 4908036883554989015}}
                moves[42] = {"_name": "move_attackRanged_jetfire_handGun_right_01", "_animStateName": "Base.RangedAttack01", "_asset": {"m_FileID": 3, "m_PathID": 4026438278308373272}}
                moves[43] = {"_name": "move_attackRanged_jetfire_handGun_right_02", "_animStateName": "Base.RangedAttack02", "_asset": {"m_FileID": 3, "m_PathID": -3609132228276371244}}
                moves[44] = {"_name": "move_attackRanged_jetfire_handGun_right_03", "_animStateName": "Base.RangedAttack03", "_asset": {"m_FileID": 3, "m_PathID": -4303718209525360164}}
                tree["_moves"] = moves
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
                print("[+] Successfully re-wired MoveSet with Drift S1 (-6173328959056132852) and Windblade S2 (-6524404075124180520)!")
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
            elif tname == "wpns_RAOE":
                data_obj = obj.read()
                data_obj.m_TextureFormat = 4
                data_obj.image = final_raoe_img
                data_obj.save()
                print("[+] Successfully injected 4-channel wpns_RAOE (RGBA32) with Emissive Mask!")
            else:
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
        elif obj.path_id == 6381148994484861096 and obj.type.name == "Material":
            tree = obj.read_typetree()
            saved_props = tree.get("m_SavedProperties", {})
            new_colors = []
            for c in saved_props.get("m_Colors", []):
                if c[0] == "_emissive_intensity_col":
                    new_colors.append((c[0], {"r": 0.1, "g": 0.7, "b": 1.0, "a": 1.0}))
                else:
                    new_colors.append(c)
            saved_props["m_Colors"] = new_colors

            new_floats = []
            for f in saved_props.get("m_Floats", []):
                if f[0] == "_emissive_overbright_range":
                    new_floats.append((f[0], 120.0))
                elif f[0] == "_emissive_pulse_intensity_range":
                    new_floats.append((f[0], 0.25))
                elif f[0] == "_emissive_pulse_time_range":
                    new_floats.append((f[0], 1.2))
                elif f[0] == "_emissive_ramp_range":
                    new_floats.append((f[0], 0.7))
                elif f[0] == "_emissive_range":
                    new_floats.append((f[0], 1.0))
                else:
                    new_floats.append(f)
            saved_props["m_Floats"] = new_floats
            tree["m_SavedProperties"] = saved_props
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured weapon Material with glowing cybertronian cyan-blue emissive effect!")
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
            if gname == "gun":
                pass
            elif "cha_jetfire_gs_leader2014_wpns_rifle_right" in gname:
                tree["m_Name"] = "cha_starsaber_gs_leader2014_wpns_sword"
            elif any(p in gname.lower() for p in ["projectile", "muzzle_flash", "gun_charge", "impact", "ironman_beam"]):
                pass
            elif "jetfire" in gname.lower():
                tree["m_Name"] = gname.replace("Jetfire", "StarSaber").replace("jetfire", "starsaber")
            tree["m_IsActive"] = True
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

    if not args.input and not (Path("extracted_apk") / "assets/assetpack").is_dir():
        print("Error: No base APK specified and extracted_apk/ not found. Provide one with --input path/to/com.kabam.bigrobot_9.2.0.apk")
        sys.exit(1)

    generate_starsaber_assets(args.input, args.output)



if __name__ == "__main__":
    main()
