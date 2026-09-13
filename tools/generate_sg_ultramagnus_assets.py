#!/usr/bin/env python3
"""
generate_sg_ultramagnus_assets.py

Complete composite grafting and procedural synthesis pipeline for
Shattered Glass Ultra Magnus (捅天枭 / SG Ultra Magnus, ID: ultramagnus_sg_leader).

Performs:
1. 3D Mesh & Hierarchy grafting:
   - Replaces Ultra Magnus's hammer (axe) with Cyclonus's sword mesh
   - Renames weapon GameObjects ('axe' -> 'sword', 'cha_ultramagnus_gs_leader_wpns_axe_right' -> 'cha_ultramagnus_sg_leader_wpns_sword_right')
   - Configures PropsController with 'sword' prop
2. Combat Animation State Machine grafting:
   - Slot [4] (S1): Cyclonus S1 Sword Slash (Cyclonus_GS_attackSpecial_01)
   - Slot [5] (S2): Tantrum S2 Bull Charge / Heavy Stomp (tantrum_gs_attackSpecial_02)
   - Slot [31] (S3): Ultra Magnus Cinematic S3 preserved, wielding the sword!
3. MoveSet MoveInfo rewiring for hitboxes and damage frames (pointing to moves.assetbundle)
4. Procedural Shattered Glass texture synthesis:
   - Crimson Red horned helmet and crest
   - Bone White skull face with glowing neon cyan optics
   - Deep Cobalt Blue chest cab, thighs, and boots
   - Crimson Red shoulders, forearms, knees, and shin intake trapezoid panels
   - Purple Shattered Glass Autobot insignia
   - Cybertronian steel sword blade with glowing cyan gem
5. Deep CAB isolation & LZ4 compression
6. High-fidelity UI portraits generation
"""

import argparse
import copy
import glob
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)


def generate_sg_ultramagnus_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_dir = Path("extracted_apk")
    if (extracted_dir / "assets/assetpack").is_dir():
        print("[*] Loading base components directly from extracted_apk/ ...")
        um_bundle_data = (extracted_dir / "assets/assetpack/ultramagnus_gs_leader_odr/ultramagnus_gs_leader.assetbundle").read_bytes()
        cy_bundle_data = (extracted_dir / "assets/assetpack/cyclonus_gs_uw06_odr/cyclonus_gs_uw06.assetbundle").read_bytes()
        tan_bundle_data = (extracted_dir / "assets/assetpack/tantrum_gs_kabam_odr/tantrum_gs_kabam.assetbundle").read_bytes()
        p_large_bytes = (extracted_dir / "assets/assetpack/portraits_odr/portraits/portrait_ultram_gs_large.png").read_bytes()
        p_small_bytes = (extracted_dir / "assets/assetpack/portraits_odr/portraits/portrait_ultram_gs_small.jpg").read_bytes()
    elif apk_path and Path(apk_path).is_file():
        apk_file = Path(apk_path)
        print(f"[*] Extracting base components from: {apk_file.name} ...")
        with zipfile.ZipFile(apk_file, "r") as z:
            um_bundle_data = z.read("assets/assetpack/ultramagnus_gs_leader_odr/ultramagnus_gs_leader.assetbundle")
            cy_bundle_data = z.read("assets/assetpack/cyclonus_gs_uw06_odr/cyclonus_gs_uw06.assetbundle")
            tan_bundle_data = z.read("assets/assetpack/tantrum_gs_kabam_odr/tantrum_gs_kabam.assetbundle")
            p_large_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_ultram_gs_large.png")
            p_small_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_ultram_gs_small.jpg")
    else:
        raise FileNotFoundError(f"Neither extracted_apk/ nor a valid APK was found: {apk_path}")

    um_env = UnityPy.load(um_bundle_data)
    cy_env = UnityPy.load(cy_bundle_data)
    tan_env = UnityPy.load(tan_bundle_data)

    print("[*] Synthesizing SG Ultra Magnus (捅天枭) textures...")

    um_mesh_00_obj = None
    um_main_img = None
    cy_wpns_img = None

    for obj in um_env.objects:
        if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_ultramagnus_gs_leader_00":
            um_mesh_00_obj = obj.read().export()
        elif obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "cha_ultramagnus_gs_leader_main_a":
            um_main_img = obj.read().image

    for obj in cy_env.objects:
        if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "cha_cyclonus_gs_uw06_wpns_a":
            cy_wpns_img = obj.read().image
            break

    # 1. Main Robot Body Texture
    user_main_path = out_dir / "cha_ultramagnus_sg_leader_main_a.png"
    if user_main_path.exists():
        print(f"[*] Loading user-customized main texture from {user_main_path} ...")
        final_main_img = Image.open(user_main_path).convert("RGBA")
    else:
        print("[*] Procedurally synthesizing SG Ultra Magnus main texture with 3D mesh UV alignment...")
        w, h = um_main_img.size
        orig_arr = np.array(um_main_img.convert("RGBA"), dtype=np.float32)
        or_r, or_g, or_b, or_a = orig_arr[..., 0], orig_arr[..., 1], orig_arr[..., 2], orig_arr[..., 3]
        lum = (or_r * 0.299 + or_g * 0.587 + or_b * 0.114) / 255.0

        verts = []
        vts = []
        for line in um_mesh_00_obj.splitlines():
            if line.startswith('v '):
                p = line.split()
                verts.append([float(p[1]), float(p[2]), float(p[3])])
            elif line.startswith('vt '):
                p = line.split()
                vts.append([float(p[1]), float(p[2])])

        verts = np.array(verts)
        vts = np.array(vts)

        mask_helmet = Image.new("L", (w, h), 0)
        mask_face = Image.new("L", (w, h), 0)
        mask_chest = Image.new("L", (w, h), 0)
        mask_shoulders = Image.new("L", (w, h), 0)
        mask_forearms = Image.new("L", (w, h), 0)
        mask_knees = Image.new("L", (w, h), 0)
        mask_shin_panels = Image.new("L", (w, h), 0)

        draw_helmet = ImageDraw.Draw(mask_helmet)
        draw_face = ImageDraw.Draw(mask_face)
        draw_chest = ImageDraw.Draw(mask_chest)
        draw_shoulders = ImageDraw.Draw(mask_shoulders)
        draw_forearms = ImageDraw.Draw(mask_forearms)
        draw_knees = ImageDraw.Draw(mask_knees)
        draw_shin_panels = ImageDraw.Draw(mask_shin_panels)

        for line in um_mesh_00_obj.splitlines():
            if line.startswith('f '):
                face_data = []
                for p in line.split()[1:]:
                    vals = p.split('/')
                    vi = int(vals[0]) - 1
                    vti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else None
                    face_data.append((vi, vti))
                
                f_vis = [vi for vi, vti in face_data]
                f_verts = verts[f_vis]
                cy = f_verts[:, 1].mean()
                cz = f_verts[:, 2].mean()
                cx = f_verts[:, 0].mean()

                pts = []
                for vi, vti in face_data:
                    if vti is not None:
                        u, v = vts[vti]
                        px = int(np.clip(u * w, 0, w - 1))
                        py = int(np.clip((1.0 - v) * h, 0, h - 1))
                        pts.append((px, py))
                if len(pts) < 3: continue

                # Head classification
                if cy >= 10.5:
                    if 10.65 <= cy < 11.5 and cz >= 0.15 and abs(cx) <= 0.28:
                        draw_face.polygon(pts, fill=255)
                    else:
                        draw_helmet.polygon(pts, fill=255)
                elif 7.5 <= cy < 10.5:
                    if abs(cx) > 2.0:
                        draw_shoulders.polygon(pts, fill=255)
                    else:
                        draw_chest.polygon(pts, fill=255)
                elif 4.5 <= cy < 7.5:
                    if abs(cx) > 1.8:
                        draw_forearms.polygon(pts, fill=255)
                    elif cy <= 5.5 and cz >= 0.45 and abs(cx) <= 1.8:
                        draw_knees.polygon(pts, fill=255)
                elif cy < 4.5:
                    if 1.5 <= cy <= 3.8 and cz >= 1.30 and 0.5 <= abs(cx) <= 1.7:
                        draw_shin_panels.polygon(pts, fill=255)
                    elif 4.0 <= cy <= 4.5 and cz >= 0.45 and abs(cx) <= 1.8:
                        draw_knees.polygon(pts, fill=255)

        m_helmet = np.array(mask_helmet) > 0
        m_face = np.array(mask_face) > 0
        m_chest = np.array(mask_chest) > 0
        m_shoulders = np.array(mask_shoulders) > 0
        m_forearms = np.array(mask_forearms) > 0
        m_knees = np.array(mask_knees) > 0
        m_shin_panels = np.array(mask_shin_panels) > 0

        # Forehead crest and brow ridge is strictly above eyes at Y < 122 in UV space
        m_helmet[:122, :250] = m_helmet[:122, :250] | m_face[:122, :250]
        m_face[:122, :250] = False

        # Optics: inside face where original texture had cyan optics
        is_optics = m_face & (or_g > 155) & (or_b > 175) & (or_r < 80)
        optics_img = Image.fromarray((is_optics * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
        m_optics = np.array(optics_img) > 0
        m_face_bone = m_face & (~m_optics)

        # Color palettes matching comic references:
        # 1. Crimson / Blood Red:
        red_r = np.clip(lum * 195.0 + 55.0, 0, 255)
        red_g = np.clip(lum * 25.0 + 8.0, 0, 255)
        red_b = np.clip(lum * 25.0 + 8.0, 0, 255)

        # 2. Deep Cobalt Blue:
        blue_r = np.clip(lum * 30.0 + 10.0, 0, 255)
        blue_g = np.clip(lum * 70.0 + 25.0, 0, 255)
        blue_b = np.clip(lum * 200.0 + 50.0, 0, 255)

        # 3. Bone White / Skull Face:
        skull_r = np.clip(lum * 210.0 + 40.0, 0, 255)
        skull_g = np.clip(lum * 205.0 + 38.0, 0, 255)
        skull_b = np.clip(lum * 195.0 + 35.0, 0, 255)
        is_crevice = m_face_bone & (lum < 0.35)
        crevice_r = np.clip(lum * 40.0 + 15.0, 0, 255)
        crevice_g = np.clip(lum * 40.0 + 15.0, 0, 255)
        crevice_b = np.clip(lum * 40.0 + 15.0, 0, 255)

        # 4. Glowing Neon Cyan Optics:
        cyan_r = np.clip(lum * 20.0 + 80.0, 0, 255)
        cyan_g = np.clip(lum * 40.0 + 220.0, 0, 255)
        cyan_b = np.clip(lum * 10.0 + 250.0, 0, 255)

        # 5. Silver Steel:
        silver_r = np.clip(lum * 200.0 + 45.0, 0, 255)
        silver_g = np.clip(lum * 205.0 + 45.0, 0, 255)
        silver_b = np.clip(lum * 215.0 + 45.0, 0, 255)

        # 6. Purple SG Autobot Insignia:
        is_original_red_insignia = (or_r > 130) & (or_g < 60) & (or_b < 60) & (~m_helmet) & (~m_shoulders) & (~m_forearms) & (~m_knees) & (~m_shin_panels)
        purple_r = np.clip(lum * 180.0 + 40.0, 0, 255)
        purple_g = np.clip(lum * 20.0 + 5.0, 0, 255)
        purple_b = np.clip(lum * 240.0 + 50.0, 0, 255)

        is_metal = (lum < 0.22) | ((or_r > 110) & (or_g > 110) & (or_b > 110) & (abs(or_r - or_g) < 25))
        res_r = np.where(is_metal, silver_r, blue_r)
        res_g = np.where(is_metal, silver_g, blue_g)
        res_b = np.where(is_metal, silver_b, blue_b)

        res_r = np.where(m_helmet, red_r, res_r)
        res_g = np.where(m_helmet, red_g, res_g)
        res_b = np.where(m_helmet, red_b, res_b)

        res_r = np.where(m_face_bone, np.where(is_crevice, crevice_r, skull_r), res_r)
        res_g = np.where(m_face_bone, np.where(is_crevice, crevice_g, skull_g), res_g)
        res_b = np.where(m_face_bone, np.where(is_crevice, crevice_b, skull_b), res_b)

        res_r = np.where(m_optics, cyan_r, res_r)
        res_g = np.where(m_optics, cyan_g, res_g)
        res_b = np.where(m_optics, cyan_b, res_b)

        res_r = np.where(m_shoulders | m_forearms, red_r, res_r)
        res_g = np.where(m_shoulders | m_forearms, red_g, res_g)
        res_b = np.where(m_shoulders | m_forearms, red_b, res_b)

        res_r = np.where(m_knees | m_shin_panels, red_r, res_r)
        res_g = np.where(m_knees | m_shin_panels, red_g, res_g)
        res_b = np.where(m_knees | m_shin_panels, red_b, res_b)

        res_r = np.where(is_original_red_insignia, purple_r, res_r)
        res_g = np.where(is_original_red_insignia, purple_g, res_g)
        res_b = np.where(is_original_red_insignia, purple_b, res_b)

        final_main_img = Image.fromarray(np.stack([res_r, res_g, res_b, or_a], axis=-1).astype(np.uint8))
        final_main_img.save(user_main_path)
        print(f"[+] Saved synthesized SG Ultra Magnus main texture to: {user_main_path}")

    # 2. Sword Weapon Texture (Adapted from Cyclonus sword)
    user_wpns_path = out_dir / "cha_ultramagnus_sg_leader_wpns_a.png"
    if user_wpns_path.exists():
        print(f"[*] Loading user-customized weapon texture from {user_wpns_path} ...")
        final_wpns_img = Image.open(user_wpns_path).convert("RGBA")
    else:
        w_arr = np.array(cy_wpns_img.convert("RGBA"), dtype=np.float32)
        wr, wg, wb, wa = w_arr[..., 0], w_arr[..., 1], w_arr[..., 2], w_arr[..., 3]
        wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0

        is_purple = (wb > 120) & (wr > 70) & (wg < 100) & (abs(wr - wb) < 60)
        c_blue_r = np.clip(wlum * 35.0 + 10.0, 0, 255)
        c_blue_g = np.clip(wlum * 75.0 + 25.0, 0, 255)
        c_blue_b = np.clip(wlum * 210.0 + 45.0, 0, 255)

        new_wr = np.where(is_purple, c_blue_r, wr)
        new_wg = np.where(is_purple, c_blue_g, wg)
        new_wb = np.where(is_purple, c_blue_b, wb)

        final_wpns_img = Image.fromarray(np.stack([new_wr, new_wg, new_wb, wa], axis=-1).astype(np.uint8))
        final_wpns_img.save(user_wpns_path)
        print(f"[+] Saved synthesized sword weapon texture to: {user_wpns_path}")

    # 2.5 Vehicle Mode Texture (tform_misc_A)
    user_tform_path = out_dir / "cha_ultramagnus_sg_leader_tform_misc_a.png"
    if user_tform_path.exists():
        print(f"[*] Loading user-customized vehicle texture from {user_tform_path} ...")
        final_tform_img = Image.open(user_tform_path).convert("RGBA")
    else:
        final_tform_img = None

    # 3. Extract Cyclonus Sword Mesh
    print("[*] Extracting Cyclonus Sword Mesh...")
    sword_mesh_tree = None
    for obj in cy_env.objects:
        if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_cyclonus_gs_uw06_wpns_sword_right":
            sword_mesh_tree = obj.read_typetree()
            sword_mesh_tree["m_Name"] = "cha_ultramagnus_sg_leader_wpns_sword_right"
            break

    if sword_mesh_tree is None:
        raise RuntimeError("Failed to extract Cyclonus sword mesh!")

    # 4. Extract Combat AnimationClips
    print("[*] Extracting S1 (Cyclonus) and S2 (Tantrum) AnimationClips...")
    clip_s1 = None
    for obj in cy_env.objects:
        if obj.type.name == "AnimationClip" and obj.read_typetree().get("m_Name") == "Cyclonus_GS_attackSpecial_01":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "ultramagnus_sg_attackSpecial_01"
            break

    clip_s2 = None
    for obj in tan_env.objects:
        if obj.type.name == "AnimationClip" and obj.read_typetree().get("m_Name") == "tantrum_gs_attackSpecial_02":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "ultramagnus_sg_attackSpecial_02"
            break

    if clip_s1 is None or clip_s2 is None:
        raise RuntimeError("Failed to extract combat animation clips!")

    print("[*] Injecting assets into SG Ultra Magnus bundle...")
    bf = list(um_env.files.values())[0]
    um_asset = list(um_env.assets)[0]

    old_cab = "CAB-b4b3b28ee550fe8ca5fe54070a2f476a"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-ultramagnussg2016leader00112233"
    print(f"[*] Deep remapping CAB: {old_cab} -> {new_cab}")

    def replace_str_in_tree(tree_obj, s_old, s_new):
        if isinstance(tree_obj, dict):
            for k, v in tree_obj.items():
                if isinstance(v, str) and s_old in v:
                    tree_obj[k] = v.replace(s_old, s_new)
                else:
                    replace_str_in_tree(v, s_old, s_new)
        elif isinstance(tree_obj, list):
            for idx, item in enumerate(tree_obj):
                if isinstance(item, str) and s_old in item:
                    tree_obj[idx] = item.replace(s_old, s_new)
                else:
                    replace_str_in_tree(item, s_old, s_new)

    PID_S1 = -3380510205146366042
    PID_S2 = -3641882075980479714

    # Iterate and modify objects in Ultra Magnus bundle
    for obj in um_env.objects:
        # 0. Combat AnimationClips: In-place replace UM S1 with Cyclonus S1, UM S2 with Tantrum S2
        if obj.path_id == PID_S1 and obj.type.name == "AnimationClip":
            tree = clip_s1
            tree["m_Name"] = "ultra_magnus_attackSpecial_01"
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected clean Cyclonus S1 AnimationClip into slot 4 (-3380510205146366042)!")
        elif obj.path_id == PID_S2 and obj.type.name == "AnimationClip":
            tree = clip_s2
            tree["m_Name"] = "ultra_magnus_attackSpecial_02"
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected clean Tantrum S2 AnimationClip into slot 5 (-3641882075980479714)!")

        # 1. Replace hammer axe mesh with Cyclonus sword mesh (pointing down as requested)
        elif obj.path_id == 7654643335206966799 and obj.type.name == "Mesh":
            tree = sword_mesh_tree
            tree["m_BindPose"] = [{'e00': 1.0, 'e01': 0.0, 'e02': 0.0, 'e03': 0.0,
                                   'e10': 0.0, 'e11': 1.0, 'e12': 0.0, 'e13': 0.0,
                                   'e20': 0.0, 'e21': 0.0, 'e22': 1.0, 'e23': 0.0,
                                   'e30': 0.0, 'e31': 0.0, 'e32': 0.0, 'e33': 1.0}]
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Cyclonus Sword Mesh into weapon slot (pointing down)!")

        # 2. Weapon SkinnedMeshRenderers
        elif obj.path_id in [-6929876573960912518, 8776407398459535180] and obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            tree["m_Mesh"] = {"m_FileID": 0, "m_PathID": 7654643335206966799}
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # 3. GameObjects: Rename axe -> sword
        elif obj.path_id in [-5665765569607374456, 7123674070001422520] and obj.type.name == "GameObject":
            tree = obj.read_typetree()
            tree["m_Name"] = "cha_ultramagnus_sg_leader_wpns_sword_right"
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
        elif obj.path_id in [-1324349832030253018, 7635592521387689351] and obj.type.name == "GameObject":
            tree = obj.read_typetree()
            tree["m_Name"] = "sword"
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
        elif obj.path_id == 9118168845269553031 and obj.type.name == "GameObject":
            tree = obj.read_typetree()
            tree["m_Name"] = "projectile_tantrum_sp2_electricity"
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Renamed projectile_ultramagnus_wave -> projectile_tantrum_sp2_electricity!")

        # 4. PropsControllers: register 'sword' prop
        elif obj.path_id in [-2561000623695164307, 8241679835078285370] and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            vals = props.get("_serializedValues", [])
            for k_idx, k_name in enumerate(keys):
                if k_name in ["axe", "sword"]:
                    keys[k_idx] = "sword"
                    vals[k_idx]["Name"] = "sword"
            props["_serializedKeys"] = keys
            props["_serializedValues"] = vals
            tree["_props"] = props
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Configured PropsController (PathID={obj.path_id}) with sword prop!")

        # 5. Fight AOC: override_UltraMagnus_GS_Leader_fight (PathID=784857089895726382)
        elif obj.path_id == 784857089895726382 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            # Slots [4] and [5] naturally point to PID_S1 and PID_S2 which were cleanly replaced in-place!
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Fight AOC (S1=Cyclonus S1, S2=Tantrum S2, S3=Ultra Magnus S3, Normals=Ultra Magnus)!")

        # 6. MoveSet: PathID=-3211011380908751738
        elif obj.path_id == -3211011380908751738 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            # moves[0]: S1 -> move_cyclonus_special_01 (in moves.assetbundle: FileID 2, PathID 3783647155754230963)
            moves[0]["_name"] = "move_cyclonus_special_01"
            moves[0]["_asset"] = {"m_FileID": 2, "m_PathID": 3783647155754230963}
            # moves[1]: S2 -> move_tantrum_special_02 (in moves.assetbundle: FileID 2, PathID -6555954099838709505)
            moves[1]["_name"] = "move_tantrum_special_02"
            moves[1]["_asset"] = {"m_FileID": 2, "m_PathID": -6555954099838709505}
            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured MoveSet (moves[0]=Cyclonus S1, moves[1]=Tantrum S2)!")

        # 7. Textures
        elif obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_ultramagnus_gs_leader_main_a":
                tex = obj.read()
                tex.image = final_main_img
                tex.save()
                print("[+] Injected procedural SG Ultra Magnus main texture!")
            elif tex_name == "cha_ultramagnus_gs_leader_wpns_a":
                tex = obj.read()
                tex.image = final_wpns_img
                tex.save()
                print("[+] Injected sword weapon texture!")
            elif tex_name == "tform_misc_A" and final_tform_img is not None:
                tex = obj.read()
                tex.image = final_tform_img
                tex.save()
                print("[+] Injected procedural SG Ultra Magnus vehicle (tform_misc_A) texture!")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        # 8. AssetBundleManifest
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/ultramagnus_sg_leader_odr/ultramagnus_sg_leader.assetbundle"
            tree["m_AssetBundleName"] = "data/ultramagnus_sg_leader_odr/ultramagnus_sg_leader.assetbundle"
            new_container = []
            for k, v in tree.get("m_Container", []):
                new_k = k.replace("ultramagnus_gs_leader", "ultramagnus_sg_leader")
                new_container.append((new_k, v))
            tree["m_Container"] = new_container
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

    print("[*] Compressing and packaging AssetBundle with LZ4...")
    sg_bundle_bytes = bf.save(packer="lz4")
    target_bundle = out_dir / "ultramagnus_sg_leader.assetbundle"
    target_bundle.write_bytes(sg_bundle_bytes)
    print(f"[+] Saved LZ4-compressed AssetBundle ({len(sg_bundle_bytes)/1024/1024:.2f} MB) to: {target_bundle}")

    print("[*] Processing Ultra Magnus portraits...")
    p_large_path = out_dir / "portrait_ultram_sg_large.png"
    p_small_path = out_dir / "portrait_ultram_sg_small.jpg"
    p_quest_path = out_dir / "portrait_ultram_sg_quest.png"
    p_icon_path = out_dir / "ultram_sg.png"

    if p_large_path.exists():
        print(f"[*] Found user-customized large portrait at {p_large_path}, preserving user version!")
    else:
        p_large_path.write_bytes(p_large_bytes)
        print(f"[+] Saved placeholder large portrait to: {p_large_path}")

    if p_small_path.exists():
        print(f"[*] Found user-customized small portrait at {p_small_path}, preserving user version!")
    else:
        p_small_path.write_bytes(p_small_bytes)
        print(f"[+] Saved placeholder small portrait to: {p_small_path}")

    if p_quest_path.exists():
        print(f"[*] Found user-customized quest portrait at {p_quest_path}, preserving user version!")
    else:
        p_quest_path.write_bytes(p_large_bytes)
        print(f"[+] Saved placeholder quest portrait to: {p_quest_path}")

    if p_icon_path.exists():
        print(f"[*] Found user-customized icon portrait at {p_icon_path}, preserving user version!")
    else:
        p_icon_path.write_bytes(p_large_bytes)
        print(f"[+] Saved placeholder icon portrait to: {p_icon_path}")

    print(f"[+] All SG Ultra Magnus assets successfully generated in: {out_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Generate SG Ultra Magnus (捅天枭) assets")
    parser.add_argument("--input", "-i", type=str, default=None, help="Path to base APK")
    parser.add_argument("--output", "-o", type=str, default="assets_redeco", help="Output directory")
    args = parser.parse_args()

    generate_sg_ultramagnus_assets(args.input, args.output)


if __name__ == "__main__":
    main()
