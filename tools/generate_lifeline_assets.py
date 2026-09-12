#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_lifeline_assets.py

Complete composite grafting and redeco pipeline for Autobot Paradron Medic Lifeline (回春手).
Features:
1. Dual Swords Armed by Default:
   - In PropsController, sets swordLeft and swordRight InitFlags to -25 (Gameplay | Frontend | MatineeReactor)
   - Permanently wields dual blades in 3D showroom and battle stances
2. Stitched Moveset & Animation State Machine:
   - Heavy (重击): Arcee Heavy (Preserved)
   - S1: Kickback S1 (kickback_gs_attackSpecial_01 -> move_kickback_special_01)
   - S2: Ratchet S2 (ratchet_gs_attackSpecial_02 -> move_ratchet_special_02)
   - L1: Windblade L1 (Windblade L1 -> move_sword_attack_light_01)
   - L2: Bonecrusher L1 (Feral L1 -> move_feral_attack_light_02)
   - L3: Rhinox L3 (tactical2_normal_attackLight_03_lowkick_R -> move_military_attack_light_03)
   - L4: Windblade L4 (Windblade L4 -> move_sword_attack_light_04)
   - M1: Optimus Primal M1 (OPtimusPrimal_BW_attackMedium_01_smash -> move_primal_attack_medium_01)
   - M2: Bonecrusher M2 (Feral M2 -> move_feral_attack_medium_02)
3. Color Scheme:
   - Clean porcelain white + Tiffany/mint seafoam green (#4EB89E) + metallic silver blade accents
   - Recolor robot main body and vehicle mode (tform_misc_A)
4. Deep CAB Isolation:
   - Independent CAB namespace CAB-5f6e7d8c9b0a123456789abcdef01234
5. UI & Dialogue Portraits:
   - Copies Arcee's portraits as placeholders for artists to replace

Usage:
    python tools/generate_lifeline_assets.py
"""

import argparse
import copy
import glob
import json
import os
import sys
import zipfile
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)


def make_zero_scale_curve(bone_path: str, duration: float) -> dict:
    return {
        "path": bone_path,
        "curve": {
            "m_Curve": [
                {
                    "time": 0.0,
                    "value": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "inSlope": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "outSlope": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "weightedMode": 0,
                    "inWeight": {"x": 0.33333334, "y": 0.33333334, "z": 0.33333334},
                    "outWeight": {"x": 0.33333334, "y": 0.33333334, "z": 0.33333334}
                },
                {
                    "time": duration,
                    "value": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "inSlope": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "outSlope": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "weightedMode": 0,
                    "inWeight": {"x": 0.33333334, "y": 0.33333334, "z": 0.33333334},
                    "outWeight": {"x": 0.33333334, "y": 0.33333334, "z": 0.33333334}
                }
            ],
            "m_PreInfinity": 2,
            "m_PostInfinity": 2,
            "m_RotationOrder": 4
        }
    }


LIFELINE_S1_PID = -8888888888888888881
LIFELINE_S2_PID = -8888888888888888882


def patch_character_fx_assetbundle(cfx_bundle_data: bytes, out_dir: Path) -> None:
    print("[*] Patching character_fx.assetbundle with high-velocity long-range laser beam...")
    cfx_env = UnityPy.load(cfx_bundle_data)
    patched = 0

    for pid in [-3275282738736286132, 1824103235525829645]:
        for o in cfx_env.objects:
            if o.path_id == pid:
                go = o.read_typetree()
                for comp in go.get("m_Component", []):
                    cid = comp.get("component", {}).get("m_PathID")
                    for o2 in cfx_env.objects:
                        if o2.path_id == cid:
                            if o2.type.name == "ParticleSystem":
                                ps = o2.read_typetree()
                                ps["InitialModule"]["startSpeed"]["scalar"] = 50.0
                                ps["InitialModule"]["startLifetime"]["scalar"] = 0.55
                                ps["lengthInSec"] = 0.55
                                ps["EmissionModule"]["rateOverTime"]["scalar"] = 12.0
                                o2.save_typetree(ps)
                                patched += 1
                            elif o2.type.name == "ParticleSystemRenderer":
                                psr = o2.read_typetree()
                                psr["m_MaxParticleSize"] = 10.0
                                psr["m_LengthScale"] = 0.35
                                o2.save_typetree(psr)
                                patched += 1

    if patched > 0:
        saved_cfx = cfx_env.file.save()
        cfx_out = out_dir / "character_fx.assetbundle"
        cfx_out.write_bytes(saved_cfx)
        print(f"[+] Successfully saved patched character_fx.assetbundle ({len(saved_cfx)} bytes) with long-range laser beam to {cfx_out}")
    else:
        print("[-] Warning: Failed to patch character_fx.assetbundle!")


def patch_moves_assetbundle(moves_bundle_data: bytes, out_dir: Path) -> None:
    print("[*] Patching moves.assetbundle with dedicated Lifeline moves...")
    moves_env = UnityPy.load(moves_bundle_data)
    moves_file = list(moves_env.file.files.values())[0]

    ab_obj = None
    for obj in moves_env.objects:
        if obj.type.name == "AssetBundle":
            ab_obj = obj
            break

    kb_reader = moves_file.objects[7117130594397893526]
    rt_reader = moves_file.objects[-6948591784739340340]

    # Clone Lifeline S1 (based on Kickback S1)
    s1_move = copy.deepcopy(kb_reader.read_typetree())
    s1_move["m_Name"] = "move_lifeline_special_01"
    s1_data = json.loads(s1_move["m_Script"])
    s1_data["moves"]["m_Name"] = "move_lifeline_special_01"

    for ev in s1_data.get("moves", {}).get("events", []):
        pn = ev.get("pn", "")
        if "laser_beam" in pn:
            ev["pn"] = "fx_p_laser_beam"
            ev["dn"] = "fx_p_laser_beam"
            ev["d"] = 15
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = -0.8
                ev["po"]["o"]["y"] = 0.0
                ev["po"]["o"]["z"] = 0.25
            if "ro" in ev and "o" in ev["ro"]:
                is_mirrored = any(
                    sc.get("type") == "MoveEventCondition_IsMirrored" and sc.get("inv") is False
                    for sc in ev.get("sc", [])
                )
                ev["ro"]["o"]["x"] = 0.0
                ev["ro"]["o"]["z"] = 0.0
                ev["ro"]["o"]["y"] = 290.0 if is_mirrored else 110.0
        elif "dash" in pn:
            ev["pn"] = "fx_r_dash_trail"

    s1_move["m_Script"] = json.dumps(s1_data)
    s1_reader = copy.copy(kb_reader)
    s1_reader.path_id = LIFELINE_S1_PID
    moves_file.objects[LIFELINE_S1_PID] = s1_reader
    s1_reader.save_typetree(s1_move)

    # Clone Lifeline S2 (based on Ratchet S2)
    s2_move = copy.deepcopy(rt_reader.read_typetree())
    s2_move["m_Name"] = "move_lifeline_special_02"
    s2_data = json.loads(s2_move["m_Script"])
    s2_data["moves"]["m_Name"] = "move_lifeline_special_02"

    for ev in s2_data.get("moves", {}).get("events", []):
        pn = ev.get("pn", "")
        if "powerup_ring" in pn:
            ev["pn"] = "fx_p_laser_beam_particulates_circle"
            ev["dn"] = "fx_p_laser_beam_particulates_circle"
            ev["d"] = 45
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = 0.0
                ev["po"]["o"]["y"] = 1.2
                ev["po"]["o"]["z"] = 0.0
        elif "powerup" in pn:
            ev["pn"] = "fx_p_shockwave_powerup"
            ev["dn"] = "fx_p_shockwave_powerup"
            ev["d"] = 30
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = 0.0
                ev["po"]["o"]["y"] = 1.2
                ev["po"]["o"]["z"] = 0.0
        elif "body_charge" in pn:
            ev["pn"] = "fx_p_shockwave_body_charge"
        elif "chest_charge" in pn:
            ev["pn"] = "fx_p_blast_charge"
        elif "wrench_blur" in pn:
            ev["pn"] = "fx_r_arcee_trail"

        # Rewire props from Ratchet's guns/wrenches to Lifeline's swords
        if ev.get("type") == "PropMoveEvent":
            if ev.get("p") == "wrench":
                ev["p"] = "swordRight"
            elif ev.get("p") == "leftGun":
                ev["p"] = "swordLeft"
        elif ev.get("type") == "PlayPropAnimatorStateMoveEvent":
            if ev.get("pn") == "wrench":
                ev["pn"] = "swordRight"

        s_ev = json.dumps(ev)
        if "leftGun" in s_ev or "wrench" in s_ev:
            s_ev = s_ev.replace("leftGun/Reference/COG/FX", "swordLeft")
            s_ev = s_ev.replace("wrench/cha_ratchet_gs_kabam_wpns_wrench", "swordRight")
            ev.clear()
            ev.update(json.loads(s_ev))

    s2_move["m_Script"] = json.dumps(s2_data)
    s2_reader = copy.copy(rt_reader)
    s2_reader.path_id = LIFELINE_S2_PID
    moves_file.objects[LIFELINE_S2_PID] = s2_reader
    s2_reader.save_typetree(s2_move)

    if ab_obj:
        ab_tree = ab_obj.read_typetree()
        container = ab_tree.get("m_Container", [])
        container = [c for c in container if "move_lifeline_special" not in c[0]]
        container.append([
            "assets/bundles/movedata/move_lifeline_special_01.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": LIFELINE_S1_PID}}
        ])
        container.append([
            "assets/bundles/movedata/move_lifeline_special_02.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": LIFELINE_S2_PID}}
        ])
        ab_tree["m_Container"] = container
        ab_obj.save_typetree(ab_tree)

    saved_moves = moves_env.file.save()
    moves_out_file = out_dir / "moves.assetbundle"
    moves_out_file.write_bytes(saved_moves)
    print(f"[+] Successfully saved patched moves.assetbundle ({len(saved_moves)} bytes) with move_lifeline_special_01 & 02 to {moves_out_file}")


def generate_lifeline_assets(apk_path: str | None = None, output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_dir = Path("extracted_apk")
    if (extracted_dir / "assets/assetpack").is_dir():
        print("[*] Loading base components directly from extracted_apk/ ...")
        pack_dir = extracted_dir / "assets/assetpack"
        a_bundle_data = (pack_dir / "arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle").read_bytes()
        kb_bundle_data = (pack_dir / "kickback_gs_kabam_odr/kickback_gs_kabam.assetbundle").read_bytes()
        rt_bundle_data = (pack_dir / "ratchet_gs_kabam_odr/ratchet_gs_kabam.assetbundle").read_bytes()
        rh_bundle_data = (pack_dir / "rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle").read_bytes()
        op_bundle_data = (pack_dir / "optimusprimal_bw_mp32_odr/optimusprimal_bw_mp32.assetbundle").read_bytes()
        wb_bundle_data = (pack_dir / "windblade_gs_odr/windblade_gs.assetbundle").read_bytes()
        proc_bundle_data = (pack_dir / "characters_procedural_odr/character_anim_procedural.assetbundle").read_bytes()
        moves_bundle_data = (pack_dir / "characters/moves.assetbundle").read_bytes()
        cfx_bundle_data = (pack_dir / "characters/character_fx.assetbundle").read_bytes()
        
        p_large_bytes = (pack_dir / "portraits_odr/portraits/portrait_arcee_gs_large.png").read_bytes()
        p_small_bytes = (pack_dir / "portraits_odr/portraits/portrait_arcee_gs_small.jpg").read_bytes()
    elif apk_path and Path(apk_path).is_file():
        apk_file = Path(apk_path)
        print(f"[*] Extracting base components from APK: {apk_file.name} ...")
        with zipfile.ZipFile(apk_file, "r") as z:
            a_bundle_data = z.read("assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
            kb_bundle_data = z.read("assets/assetpack/kickback_gs_kabam_odr/kickback_gs_kabam.assetbundle")
            rt_bundle_data = z.read("assets/assetpack/ratchet_gs_kabam_odr/ratchet_gs_kabam.assetbundle")
            rh_bundle_data = z.read("assets/assetpack/rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle")
            op_bundle_data = z.read("assets/assetpack/optimusprimal_bw_mp32_odr/optimusprimal_bw_mp32.assetbundle")
            wb_bundle_data = z.read("assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle")
            proc_bundle_data = z.read("assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle")
            moves_bundle_data = z.read("assets/assetpack/characters/moves.assetbundle")
            cfx_bundle_data = z.read("assets/assetpack/characters/character_fx.assetbundle")
            p_large_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_arcee_gs_large.png")
            p_small_bytes = z.read("assets/assetpack/portraits_odr/portraits/portrait_arcee_gs_small.jpg")
    else:
        raise FileNotFoundError(f"Neither extracted_apk/ nor a valid APK was found: {apk_path}")

    # Patch moves.assetbundle and character_fx.assetbundle
    patch_moves_assetbundle(moves_bundle_data, out_dir)
    patch_character_fx_assetbundle(cfx_bundle_data, out_dir)

    a_env = UnityPy.load(a_bundle_data)
    kb_env = UnityPy.load(kb_bundle_data)
    rt_env = UnityPy.load(rt_bundle_data)
    rh_env = UnityPy.load(rh_bundle_data)
    op_env = UnityPy.load(op_bundle_data)
    wb_env = UnityPy.load(wb_bundle_data)
    proc_env = UnityPy.load(proc_bundle_data)

    print("[*] Extracting donor animations...")
    # 1. Kickback S1
    kb_s1_clip_tree = None
    for obj in kb_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            if t.get("m_Name") == "kickback_gs_attackSpecial_01":
                kb_s1_clip_tree = t
                print("[+] Extracted Kickback S1 AnimationClip")
                break

    # 2. Ratchet S2
    rt_s2_clip_tree = None
    for obj in rt_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            if t.get("m_Name") == "ratchet_gs_attackSpecial_02":
                rt_s2_clip_tree = t
                print("[+] Extracted Ratchet S2 AnimationClip")
                break

    # 3. Rhinox L3
    rh_l3_clip_tree = None
    for obj in rh_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            if t.get("m_Name") == "tactical2_normal_attackLight_03_lowkick_R":
                rh_l3_clip_tree = t
                print("[+] Extracted Rhinox L3 AnimationClip")
                break

    # 4. Optimus Primal M1
    op_m1_clip_tree = None
    for obj in op_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            if t.get("m_Name") == "OPtimusPrimal_BW_attackMedium_01_smash":
                op_m1_clip_tree = t
                print("[+] Extracted Optimus Primal M1 AnimationClip")
                break



    print("[*] Synthesizing Lifeline (回春手) textures...")
    # Load or synthesize main body
    user_main_path = out_dir / "cha_lifeline_gs_deluxe2014_main_a.png"
    if user_main_path.exists():
        print(f"[*] Using existing main texture: {user_main_path}")
        final_main_img = Image.open(user_main_path).convert("RGBA")
    else:
        orig_main = None
        for obj in a_env.objects:
            if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_main_a":
                orig_main = obj.read().image
                break
        m_arr = np.array(orig_main.convert("RGBA"), dtype=np.float32)
        r, g, b, a = m_arr[..., 0], m_arr[..., 1], m_arr[..., 2], m_arr[..., 3]
        lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0

        is_pink = (r > 110) & (r > g * 1.25) & (b > 50)
        mint_r = np.clip(lum * 65.0 + 35.0, 0, 255)
        mint_g = np.clip(lum * 175.0 + 65.0, 0, 255)
        mint_b = np.clip(lum * 145.0 + 55.0, 0, 255)

        is_white = (lum > 0.6) & (~is_pink)
        white_r = np.clip(lum * 120.0 + 130.0, 0, 255)
        white_g = np.clip(lum * 120.0 + 135.0, 0, 255)
        white_b = np.clip(lum * 120.0 + 135.0, 0, 255)

        res_r = np.where(is_pink, mint_r, np.where(is_white, white_r, r))
        res_g = np.where(is_pink, mint_g, np.where(is_white, white_g, g))
        res_b = np.where(is_pink, mint_b, np.where(is_white, white_b, b))
        final_main_img = Image.fromarray(np.stack([res_r, res_g, res_b, a], axis=-1).astype(np.uint8))
        final_main_img.save(user_main_path)
        print(f"[+] Saved synthesized main texture to {user_main_path}")

    # Load or synthesize vehicle mode texture
    user_tform_path = out_dir / "cha_lifeline_gs_deluxe2014_tform_misc_a.png"
    if user_tform_path.exists():
        print(f"[*] Using existing vehicle texture: {user_tform_path}")
        final_tform_img = Image.open(user_tform_path).convert("RGBA")
    else:
        orig_tform = None
        for obj in a_env.objects:
            if obj.type.name == "Texture2D" and obj.read_typetree().get("m_Name") in ["tform_misc_A", "tform_misc_a"]:
                orig_tform = obj.read().image
                break
        t_arr = np.array(orig_tform.convert("RGBA"), dtype=np.float32)
        tr, tg, tb, ta = t_arr[..., 0], t_arr[..., 1], t_arr[..., 2], t_arr[..., 3]
        tlum = (tr * 0.299 + tg * 0.587 + tb * 0.114) / 255.0

        is_t_pink = (tr > 100) & (tr > tg * 1.2)
        t_mint_r = np.clip(tlum * 65.0 + 35.0, 0, 255)
        t_mint_g = np.clip(tlum * 175.0 + 65.0, 0, 255)
        t_mint_b = np.clip(tlum * 145.0 + 55.0, 0, 255)

        is_t_white = (tlum > 0.6) & (~is_t_pink)
        t_white_r = np.clip(tlum * 120.0 + 130.0, 0, 255)
        t_white_g = np.clip(tlum * 120.0 + 135.0, 0, 255)
        t_white_b = np.clip(tlum * 120.0 + 135.0, 0, 255)

        t_res_r = np.where(is_t_pink, t_mint_r, np.where(is_t_white, t_white_r, tr))
        t_res_g = np.where(is_t_pink, t_mint_g, np.where(is_t_white, t_white_g, tg))
        t_res_b = np.where(is_t_pink, t_mint_b, np.where(is_t_white, t_white_b, tb))
        final_tform_img = Image.fromarray(np.stack([t_res_r, t_res_g, t_res_b, ta], axis=-1).astype(np.uint8))
        final_tform_img.save(user_tform_path)
        print(f"[+] Saved synthesized vehicle texture to {user_tform_path}")

    # Load or synthesize weapons texture and 4-channel Emissive RAOE mask
    user_wpns_path = out_dir / "cha_lifeline_gs_deluxe2014_wpns_a.png"
    user_raoe_path = out_dir / "cha_lifeline_gs_deluxe2014_wpns_raoe.png"
    
    orig_wpns = None
    orig_raoe = None
    for obj in a_env.objects:
        if obj.type.name == "Texture2D":
            tname = obj.read_typetree().get("m_Name", "")
            if "wpns_a" in tname:
                orig_wpns = obj.read().image
            elif tname == "wpns_RAOE":
                orig_raoe = obj.read().image

    if user_wpns_path.exists():
        print(f"[*] Using existing weapons texture: {user_wpns_path}")
        final_wpns_img = Image.open(user_wpns_path).convert("RGBA")
    else:
        w_arr = np.array(orig_wpns.convert("RGBA"), dtype=np.float32)
        wr, wg, wb, wa = w_arr[..., 0], w_arr[..., 1], w_arr[..., 2], w_arr[..., 3]
        wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0

        # Vibrant high-tech energon blade: Tiffany / mint energon shimmer
        is_blade = (wlum > 0.6)
        blade_r = np.clip(wlum * 45.0 + 40.0, 0, 255)
        blade_g = np.clip(wlum * 150.0 + 105.0, 0, 255)
        blade_b = np.clip(wlum * 135.0 + 100.0, 0, 255)

        # Radiant core / cutting edge highlight
        is_core = (wlum > 0.82)
        core_r = np.clip(wlum * 120.0 + 130.0, 0, 255)
        core_g = np.full_like(wlum, 255.0)
        core_b = np.clip(wlum * 110.0 + 145.0, 0, 255)

        w_res_r = np.where(is_core, core_r, np.where(is_blade, blade_r, wr))
        w_res_g = np.where(is_core, core_g, np.where(is_blade, blade_g, wg))
        w_res_b = np.where(is_core, core_b, np.where(is_blade, blade_b, wb))
        final_wpns_img = Image.fromarray(np.stack([w_res_r, w_res_g, w_res_b, wa], axis=-1).astype(np.uint8))
        final_wpns_img.save(user_wpns_path)
        print(f"[+] Saved synthesized enhanced weapons texture to {user_wpns_path}")

    # Synthesize 4-channel wpns_RAOE with Emissive Alpha Mask (Star Saber technique)
    if user_raoe_path.exists():
        print(f"[*] Using existing weapons RAOE texture: {user_raoe_path}")
        final_raoe_img = Image.open(user_raoe_path).convert("RGBA")
    else:
        raoe_rgb = np.array(orig_raoe.convert("RGB"), dtype=np.uint8)
        diffuse_small = np.array(final_wpns_img.convert("RGBA").resize(orig_raoe.size, Image.Resampling.BILINEAR))
        diff_lum = (diffuse_small[..., 0] * 0.299 + diffuse_small[..., 1] * 0.587 + diffuse_small[..., 2] * 0.114) / 255.0

        # Emissive mask: blade regions glow intensely (160 ~ 255), hilt/joints stay non-emissive
        emissive_alpha = np.where(
            diff_lum > 0.55,
            np.clip((diff_lum - 0.55) / 0.45 * 195.0 + 60.0, 0, 255),
            np.clip(diff_lum * 40.0, 0, 30)
        ).astype(np.uint8)
        final_raoe_img = Image.fromarray(np.dstack([raoe_rgb, emissive_alpha]), "RGBA")
        final_raoe_img.save(user_raoe_path)
        print(f"[+] Synthesized 4-channel wpns_RAOE with Emissive Alpha mask to {user_raoe_path}")

    print("[*] Remapping CAB and isolating namespace...")
    bf = list(a_env.files.values())[0]
    old_cab = "CAB-76e93ef67dadb9a900b941c584b3142d"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-5f6e7d8c9b0a123456789abcdef01234"
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

    extra_fx = [
        {"Prefab": {"m_FileID": 2, "m_PathID": 1824103235525829645}, "Amount": 2},  # fx_p_laser_beam
        {"Prefab": {"m_FileID": 2, "m_PathID": -3275282738736286132}, "Amount": 2}, # fx_p_laser_beam
        {"Prefab": {"m_FileID": 2, "m_PathID": 8517454522441586446}, "Amount": 2},  # fx_p_laser_beam_particulates_circle
        {"Prefab": {"m_FileID": 2, "m_PathID": 2487375751371863059}, "Amount": 2},  # fx_p_laser_beam_particulates_circle
        {"Prefab": {"m_FileID": 2, "m_PathID": 8921219544835956990}, "Amount": 2},  # fx_p_shockwave_powerup
        {"Prefab": {"m_FileID": 2, "m_PathID": -3197816761895880547}, "Amount": 2}, # fx_p_shockwave_body_charge
        {"Prefab": {"m_FileID": 2, "m_PathID": -7542691667278146756}, "Amount": 2}, # fx_p_blast_charge
        {"Prefab": {"m_FileID": 2, "m_PathID": 5349134492591490934}, "Amount": 2},  # fx_p_kickback_charge_up
        {"Prefab": {"m_FileID": 2, "m_PathID": -544983064765824370}, "Amount": 2},  # fx_p_kickback_laser_impact
        {"Prefab": {"m_FileID": 2, "m_PathID": -3023499699155395231}, "Amount": 2}, # fx_r_trail_kickback
        {"Prefab": {"m_FileID": 2, "m_PathID": -7577462007175247289}, "Amount": 2}, # fx_r_dash_trail
        {"Prefab": {"m_FileID": 2, "m_PathID": 6687875466302294803}, "Amount": 2},  # fx_r_trail_bonecrusher
        {"Prefab": {"m_FileID": 2, "m_PathID": 338295113226394914}, "Amount": 2},   # fx_r_trail_windblade_small
        {"Prefab": {"m_FileID": 2, "m_PathID": -3835810417621587917}, "Amount": 2}, # fx_r_trail_red
        {"Prefab": {"m_FileID": 1, "m_PathID": -811174631493111739}, "Amount": 2},  # fx_p_foot_drag_sparks
    ]

    for obj in a_env.objects:
        # 1. PropsController: Set dual swords permanently active!
        if obj.path_id in [-8672360083464370100, -468543671400758953] and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            props = tree.get("_props", {})
            keys = props.get("_serializedKeys", [])
            vals = props.get("_serializedValues", [])
            for k_idx, k_name in enumerate(keys):
                if k_name in ["swordLeft", "swordRight"]:
                    vals[k_idx]["InitFlags"] = -25  # Gameplay | Frontend | MatineeReactor
                    vals[k_idx]["_startActive"] = True
            props["_serializedValues"] = vals
            tree["_props"] = props
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Configured PropsController (PathID={obj.path_id}) with permanent dual swords (InitFlags=-25)!")

        # 1b. PrefabLib: inject extra VFX into prewarm pool for stitched moves
        elif obj.path_id == -7737873523461476806 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            plist = tree.get("PrefabList", [])
            existing_pids = set(x["Prefab"]["m_PathID"] for x in plist)
            for ef in extra_fx:
                if ef["Prefab"]["m_PathID"] not in existing_pids:
                    plist.append(ef)
            tree["PrefabList"] = plist
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Injected extra VFX prefabs into PrefabLib (total: {len(plist)})")

        # 2. Inject AnimationClips:
        elif obj.path_id == 4962354785087291012 and obj.type.name == "AnimationClip" and kb_s1_clip_tree is not None:
            # Overwrite Arcee S1 with Kickback S1
            tree = kb_s1_clip_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Kickback S1 AnimationClip into slot 4962354785087291012")

        elif obj.path_id == 1304560969345666953 and obj.type.name == "AnimationClip" and rt_s2_clip_tree is not None:
            # Overwrite Arcee S2 with Ratchet S2
            tree = rt_s2_clip_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Ratchet S2 AnimationClip into slot 1304560969345666953")

        elif obj.path_id == -8736743575847730373 and obj.type.name == "AnimationClip" and rh_l3_clip_tree is not None:
            # Repurpose clip for Rhinox L3
            tree = rh_l3_clip_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Rhinox L3 AnimationClip into slot -8736743575847730373")

        elif obj.path_id == -565707484110939324 and obj.type.name == "AnimationClip" and op_m1_clip_tree is not None:
            # Repurpose clip for Optimus Primal M1
            tree = op_m1_clip_tree
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Injected Optimus Primal M1 AnimationClip into slot -565707484110939324")

        # 2b. Character Root MonoBehaviour: Retarget VictoryStagePrefab to Sword Victory Stage
        elif obj.path_id == 8221105282552802949 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            # Retarget VictoryStagePrefab to procedural TFormStage_Sword_Male_Victory (in FileID 8)
            tree["VictoryStagePrefab"] = {"m_FileID": 8, "m_PathID": 1484321543804849475}
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully retargeted VictoryStagePrefab to procedural TFormStage_Sword_Male_Victory!")

        # 3. AnimatorOverrideController (Fight AOC)
        elif obj.path_id == -1743739782552134489 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            # L1: Windblade L1
            clips[2]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -789203328637063267}
            # L2: Bonecrusher L1
            clips[3]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -9189341399945500108}
            # L3: Rhinox L3
            clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -8736743575847730373}
            # L4: Windblade L4
            clips[43]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 3830411807250169071}
            # M1: Optimus Primal M1
            clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -565707484110939324}
            # M2: Bonecrusher M2
            clips[44]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 835124858721742528}
            # S1: Kickback S1
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 4962354785087291012}
            # S2: Ratchet S2
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 1304560969345666953}
            # Victory: procedural sword_male_victory (in FileID 3)
            clips[39]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -3196363985734342445}
            # Victory Idle: procedural sword_male_victory_idle (in FileID 3)
            clips[40]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 3303065432090877960}
            # Heavy: Arcee Heavy preserved
            clips[58]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 1582189478597319423}
            
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully rewired fight AnimatorOverrideController with stitched moveset and sword victory overrides!")

        # 3b. Living World AnimatorOverrideController (LW AOC)
        elif obj.path_id == -3591652285783644433 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            if len(clips) > 1:
                # Slot 1 is the Victory clip in Living World
                clips[1]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -3196363985734342445}
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully rewired Living World AnimatorOverrideController with sword victory!")

        # 4. MoveSet (MonoBehaviour)
        elif obj.path_id == -4848773121996721726 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])
            # [0] Base.LightAttack01 -> Windblade L1
            moves[0] = {"_name": "move_sword_attack_light_01", "_animStateName": "Base.LightAttack01", "_asset": {"m_FileID": 7, "m_PathID": -1283304507747283112}}
            # [1] Base.LightAttack02 -> Bonecrusher L1
            moves[1] = {"_name": "move_feral_attack_light_02", "_animStateName": "Base.LightAttack02", "_asset": {"m_FileID": 7, "m_PathID": 3938142109099366006}}
            # [2] Base.LightAttack03 -> Rhinox L3
            moves[2] = {"_name": "move_military_attack_light_03", "_animStateName": "Base.LightAttack03", "_asset": {"m_FileID": 7, "m_PathID": 2319864737932337275}}
            # [3] Base.LightAttack04 -> Windblade L4
            moves[3] = {"_name": "move_sword_attack_light_04", "_animStateName": "Base.LightAttack04", "_asset": {"m_FileID": 7, "m_PathID": 4145453135915101152}}
            # [4] Base.MediumAttack01 -> Optimus Primal M1
            moves[4] = {"_name": "move_primal_attack_medium_01", "_animStateName": "Base.MediumAttack01", "_asset": {"m_FileID": 7, "m_PathID": -6973531985879257707}}
            # [5] Base.MediumAttack02 -> Bonecrusher M2
            moves[5] = {"_name": "move_feral_attack_medium_02", "_animStateName": "Base.MediumAttack02", "_asset": {"m_FileID": 7, "m_PathID": 5917300479849172794}}
            # [6] Base.SpecialAttack01 -> Lifeline S1 (Long-range horizontal visor laser beam)
            moves[6] = {"_name": "move_lifeline_special_01", "_animStateName": "Base.SpecialAttack01", "_asset": {"m_FileID": 7, "m_PathID": LIFELINE_S1_PID}}
            # [7] Base.SpecialAttack02 -> Lifeline S2 (Dual energon swords powerup)
            moves[7] = {"_name": "move_lifeline_special_02", "_animStateName": "Base.SpecialAttack02", "_asset": {"m_FileID": 7, "m_PathID": LIFELINE_S2_PID}}
            # [43] Base.HeavyAttack -> Arcee Heavy preserved
            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Successfully rewired MoveSet with stitched MoveInfo assets!")

        # 5. Textures
        elif obj.type.name == "Texture2D":
            tree = obj.read_typetree()
            tname = tree.get("m_Name", "")
            if tname == "cha_arcee_gs_deluxe2014_main_a":
                data_obj = obj.read()
                data_obj.image = final_main_img
                data_obj.save()
                print("[+] Injected Lifeline main body texture")
            elif tname in ["tform_misc_A", "tform_misc_a"]:
                data_obj = obj.read()
                data_obj.image = final_tform_img
                data_obj.save()
                print("[+] Injected Lifeline vehicle texture")
            elif "wpns_a" in tname:
                data_obj = obj.read()
                data_obj.image = final_wpns_img
                data_obj.save()
                print("[+] Injected Lifeline weapons texture")
            elif tname == "wpns_RAOE":
                data_obj = obj.read()
                data_obj.m_TextureFormat = 4  # RGBA32
                data_obj.image = final_raoe_img
                data_obj.save()
                print("[+] Injected 4-channel wpns_RAOE (RGBA32) with Emissive Alpha Mask!")
            else:
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        # 6. Weapon Material: Configure Cybertronian Glowing Emissive Aura (Star Saber feature)
        elif obj.path_id == -6330624618415323657 and obj.type.name == "Material":
            tree = obj.read_typetree()
            saved_props = tree.get("m_SavedProperties", {})
            new_colors = []
            for c in saved_props.get("m_Colors", []):
                if c[0] == "_emissive_intensity_col":
                    # Radiant Tiffany / Mint energon glow (overbright HDR bloom)
                    new_colors.append((c[0], {"r": 0.25, "g": 1.25, "b": 0.95, "a": 1.0}))
                else:
                    new_colors.append(c)
            saved_props["m_Colors"] = new_colors

            new_floats = []
            for f in saved_props.get("m_Floats", []):
                if f[0] == "_emissive_overbright_range":
                    new_floats.append((f[0], 120.0))
                elif f[0] == "_emissive_pulse_intensity_range":
                    new_floats.append((f[0], 0.35))
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
            print("[+] Configured weapon Material with glowing cybertronian mint/cyan emissive aura!")

        # 6. AssetBundle Definition
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/lifeline_gs_deluxe2014_odr/lifeline_gs_deluxe2014.assetbundle"
            tree["m_AssetBundleName"] = "data/lifeline_gs_deluxe2014_odr/lifeline_gs_deluxe2014.assetbundle"
            new_container = []
            for k, v in tree.get("m_Container", []):
                new_k = k.replace("arcee_gs_deluxe2014", "lifeline_gs_deluxe2014")
                new_container.append((new_k, v))
            tree["m_Container"] = new_container

            # Add extra FX to m_PreloadTable
            preload = tree.get("m_PreloadTable", [])
            preload_pids = set(x.get("m_PathID") for x in preload)
            for ef in extra_fx:
                ptr = ef["Prefab"]
                if ptr["m_PathID"] not in preload_pids:
                    preload.append({"m_FileID": ptr["m_FileID"], "m_PathID": ptr["m_PathID"]})
            tree["m_PreloadTable"] = preload

            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Updated AssetBundle container mappings and preload table ({len(preload)} entries)")

        # 7. GameObjects
        elif obj.type.name == "GameObject":
            tree = obj.read_typetree()
            gname = tree.get("m_Name", "")
            if "arcee" in gname.lower():
                tree["m_Name"] = gname.replace("Arcee", "Lifeline").replace("arcee", "lifeline")
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        else:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except Exception:
                pass

    # Remap CAB files
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

    bundle_bytes = bf.save(packer="lz4")
    (out_dir / "lifeline_gs_deluxe2014.assetbundle").write_bytes(bundle_bytes)
    print(f"[+] Saved lifeline_gs_deluxe2014.assetbundle ({len(bundle_bytes)} bytes) to {out_dir}/")

    # Generate Manifest
    mf_text = f"""ManifestFileVersion: 0
CRC: 0
Hashes:
  AssetFileHash:
    serializedVersion: 2
    Hash: 5f6e7d8c9b0a123456789abcdef01234
  TypeTreeHash:
    serializedVersion: 2
    Hash: 76e93ef67dadb9a900b941c584b3142d
HashAppended: 0
ClassTypes:
- Class: 1
  Script: {{instanceID: 0}}
- Class: 4
  Script: {{instanceID: 0}}
- Class: 21
  Script: {{instanceID: 0}}
- Class: 28
  Script: {{instanceID: 0}}
- Class: 43
  Script: {{instanceID: 0}}
- Class: 48
  Script: {{instanceID: 0}}
- Class: 74
  Script: {{instanceID: 0}}
- Class: 90
  Script: {{instanceID: 0}}
- Class: 91
  Script: {{instanceID: 0}}
- Class: 95
  Script: {{instanceID: 0}}
- Class: 114
  Script: {{instanceID: 0}}
- Class: 115
  Script: {{instanceID: 0}}
- Class: 137
  Script: {{instanceID: 0}}
- Class: 221
  Script: {{instanceID: 0}}
Assets:
- Assets/Bundles/Characters/Merged/Lifeline_GS_Deluxe2014/Lifeline_GS_Deluxe2014.prefab
- Assets/Bundles/Characters/Merged/Lifeline_GS_Deluxe2014/Lifeline_GS_Deluxe2014_lw.prefab
Dependencies:
- characters/character_fx.assetbundle
- characters/character_audio.assetbundle
- characters/moves.assetbundle
"""
    (out_dir / "lifeline_gs_deluxe2014.assetbundle.manifest").write_text(mf_text, encoding="utf-8")

    # Portraits Placeholders (only write if file does not already exist so user customizations are preserved)
    print("[*] Checking UI and dialogue portraits...")
    for p_name, p_bytes in [
        ("portrait_lifeline_large.png", p_large_bytes),
        ("portrait_lifeline_small.jpg", p_small_bytes),
        ("portrait_lifeline_quest.png", p_large_bytes),
        ("portrait_lifeline_gs_large.png", p_large_bytes),
        ("portrait_lifeline_gs_small.jpg", p_small_bytes),
        ("portrait_lifeline_gs_quest.png", p_large_bytes),
        ("lifeline.png", p_large_bytes),
    ]:
        target_p = out_dir / p_name
        if not target_p.exists():
            target_p.write_bytes(p_bytes)
            print(f"  [+] Created default placeholder: {p_name}")
        else:
            print(f"  [*] Preserved custom portrait: {p_name}")

    print(f"\n[SUCCESS] Lifeline (回春手) complete composite assets generated in {out_dir}/!")


def find_default_apk() -> str | None:
    candidates = glob.glob("com.kabam.bigrobot*.apk") + glob.glob("*.apk")
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(description="Generate Lifeline (回春手) complete composite assets.")
    parser.add_argument("--input", "-i", default=find_default_apk(), help="Path to base Kabam 9.2.0 APK")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory (default: assets_redeco)")
    args = parser.parse_args()

    if not args.input and not (Path("extracted_apk") / "assets/assetpack").is_dir():
        print("Error: No base APK specified and extracted_apk/ not found.")
        sys.exit(1)

    generate_lifeline_assets(args.input, args.output)


if __name__ == "__main__":
    main()
