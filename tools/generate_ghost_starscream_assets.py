#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_ghost_starscream_assets.py

Full production pipeline for 鬼魂红蜘蛛 (Ghost Starscream / starscream_ghost_gs):
1. UI Portraits setup (Starscream's original portraits copied to stars_ghost)
2. moves.assetbundle patch:
   - Preserves all 946 existing objects (including Lifeline special moves)
   - Injects dedicated Ghost Starscream ranged bursts (move_attackRanged_stars_ghost_burst_01..03)
     spawning Tantrum's flame bullet
3. starscream_ghost_gs.assetbundle synthesis:
   - Base mold: Starscream Seeker mold (cha_starscream_gs_leader2015_00 / 01)
   - Ethereal Spectral Cyan Albedo synthesized from authentic Starscream textures (cha_starscream_gs_leader2015_main_a)
   - Cockpit blazing white-cyan energy spark core synthesized from tform_misc_A
   - Translucent calf/leg fade down to feet (premultiplied alpha: 1.0 at knee -> 0.15 at feet)
   - Vivid Dark Energon Magenta/Purple eyes and Decepticon insignia
   - Full 4-channel PBR RAOE with high-intensity Emissive Alpha mask (155 base, 255 spark/eyes, 220 edge seams)
   - Star Saber caliber emissive shader tuning (120.0 overbright, 1.0 emissive range, cyan pulse 1.5s)
   - All body materials configured for Premultiplied Alpha Transparent mode (Queue 3000, _ZWrite 0)
   - Import Tantrum bullet & flame projectile, retinting materials and particles to Ghost Blue (#00E5FF)
   - Import Ramjet hovering CombatIdle and locorun
   - AOC: Ramjet hovering idle/locorun + Ramjet Waspinator melee chain + Heavy donut +
          S1 = Sideswipe S1, S2 = Starscream S1, S3 = Starscream S3
   - MoveSet: wired to Ramjet melee, Sideswipe S1, Starscream S1, and Ghost Ranged bursts
   - Deep CAB isolation and LZ4 packaging
"""

import copy
import io
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required.")
    sys.exit(1)

OUT_DIR = Path("assets_redeco")
OUT_DIR.mkdir(exist_ok=True)

GHOST_BURST_01_PID = 7730000000000000001
GHOST_BURST_02_PID = 7730000000000000002
GHOST_BURST_03_PID = 7730000000000000003

# ---------------------------------------------------------
# Step 1: Copy UI Portraits
# ---------------------------------------------------------
def setup_portraits():
    print("[*] Setting up Ghost Starscream UI Portraits...")
    src_l = Path("extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_stars_gs_large.png")
    src_s = Path("extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_stars_gs_small.jpg")
    src_d = Path("extracted_apk/assets/assetpack/dialogue_odr/dialogue/stars_gs.png")

    shutil.copy2(src_l, OUT_DIR / "portrait_stars_ghost_large.png")
    shutil.copy2(src_s, OUT_DIR / "portrait_stars_ghost_small.jpg")
    shutil.copy2(src_l, OUT_DIR / "portrait_stars_ghost_quest.png")
    if src_d.exists():
        shutil.copy2(src_d, OUT_DIR / "stars_ghost.png")
    print("    [+] Portraits copied to assets_redeco/portrait_stars_ghost_*")


# ---------------------------------------------------------
# Step 2: Patch moves.assetbundle
# ---------------------------------------------------------
def patch_moves_bundle():
    print("[*] Patching moves.assetbundle with Ghost Starscream ranged burst moves...")
    moves_path = OUT_DIR / "moves.assetbundle"
    if not moves_path.exists():
        moves_path = Path("assets_netflix/moves.assetbundle")
    
    moves_env = UnityPy.load(str(moves_path))
    moves_file = list(moves_env.file.files.values())[0]

    ab_obj = None
    for o in moves_env.objects:
        if o.type.name == "AssetBundle":
            ab_obj = o
            break

    b1_reader = moves_file.objects[-1597096583486576030]
    b2_reader = moves_file.objects[-7160565378128486076]
    b3_reader = moves_file.objects[6254266686066863405]

    def make_ghost_burst(src_reader, new_name, new_pid):
        tree = copy.deepcopy(src_reader.read_typetree())
        tree["m_Name"] = new_name
        data = json.loads(tree["m_Script"])
        data["moves"]["id"] = new_name
        for ev in data.get("moves", {}).get("events", []):
            ev["mn"] = new_name
            if ev.get("type") == "ProjectileMoveEvent":
                ev["pn"] = "projectile_tantrum_bullet"
                ev["dn"] = "projectile_tantrum_bullet"
        tree["m_Script"] = json.dumps(data)
        
        new_reader = copy.copy(src_reader)
        new_reader.path_id = new_pid
        moves_file.objects[new_pid] = new_reader
        new_reader.save_typetree(tree)

    make_ghost_burst(b1_reader, "move_attackRanged_stars_ghost_burst_01", GHOST_BURST_01_PID)
    make_ghost_burst(b2_reader, "move_attackRanged_stars_ghost_burst_02", GHOST_BURST_02_PID)
    make_ghost_burst(b3_reader, "move_attackRanged_stars_ghost_burst_03", GHOST_BURST_03_PID)

    if ab_obj:
        ab_tree = ab_obj.read_typetree()
        container = ab_tree.get("m_Container", [])
        container = [c for c in container if "stars_ghost" not in c[0]]
        container.append([
            "assets/bundles/movedata/move_attackRanged_stars_ghost_burst_01.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": GHOST_BURST_01_PID}}
        ])
        container.append([
            "assets/bundles/movedata/move_attackRanged_stars_ghost_burst_02.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": GHOST_BURST_02_PID}}
        ])
        container.append([
            "assets/bundles/movedata/move_attackRanged_stars_ghost_burst_03.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": GHOST_BURST_03_PID}}
        ])
        ab_tree["m_Container"] = container
        ab_obj.save_typetree(ab_tree)

    saved_data = moves_env.file.save(packer="lz4")
    (OUT_DIR / "moves.assetbundle").write_bytes(saved_data)
    print(f"    [+] Saved patched moves.assetbundle ({len(moves_file.objects)} objects >= 945)")


# ---------------------------------------------------------
# Step 3: Helper for recursive string replacement in typetrees
# ---------------------------------------------------------
def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in list(tree_obj.items()):
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


# ---------------------------------------------------------
# Step 4: Generate starscream_ghost_gs.assetbundle
# ---------------------------------------------------------
def generate_ghost_starscream_bundle():
    print("[*] Generating starscream_ghost_gs.assetbundle...")
    tc_bundle_path = Path("extracted_apk/assets/assetpack/thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle")
    tantrum_bundle_path = Path("extracted_apk/assets/assetpack/tantrum_gs_kabam_odr/tantrum_gs_kabam.assetbundle")
    ramjet_bundle_path = Path("extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle")
    chars_bundle_path = Path("extracted_apk/assets/assetpack/characters/characters.assetbundle")

    tc_env = UnityPy.load(str(tc_bundle_path))
    t_env = UnityPy.load(str(tantrum_bundle_path))
    r_env = UnityPy.load(str(ramjet_bundle_path))
    c_env = UnityPy.load(str(chars_bundle_path))

    tc_bf = tc_env.file
    tc_sf = None
    old_cab = None
    for name, f in tc_bf.files.items():
        if not name.endswith((".resS", ".resource")):
            tc_sf = f
            old_cab = name
            break
    
    new_cab = "CAB-7e3f0505050505050505050505050505"

    t_sf = None
    for name, f in t_env.file.files.items():
        if not name.endswith((".resS", ".resource")):
            t_sf = f
            break

    r_sf = None
    for name, f in r_env.file.files.items():
        if not name.endswith((".resS", ".resource")):
            r_sf = f
            break

    c_sf = None
    for name, f in c_env.file.files.items():
        if not name.endswith((".resS", ".resource")):
            c_sf = f
            break

    def import_object_to_tc(src_reader, class_id, script_name=None):
        new_reader = copy.copy(src_reader)
        new_reader.assets_file = tc_sf
        if class_id == 1:       # GameObject
            new_reader.type_id = 2
        elif class_id == 4:     # Transform
            new_reader.type_id = 9
        elif class_id == 21:    # Material
            new_reader.type_id = 7
        elif class_id == 198:   # ParticleSystem
            new_reader.type_id = 6
        elif class_id == 199:   # ParticleSystemRenderer
            new_reader.type_id = 5
        elif class_id == 74:    # AnimationClip
            new_reader.type_id = 44
        elif class_id == 114:   # MonoBehaviour
            type_map = {
                "Projectile": 28,
                "MoveSet": 32,
                "PrefabLib": 25,
                "MoveSequencer": 36,
            }
            new_reader.type_id = type_map.get(script_name, 3)
        tc_sf.objects[new_reader.path_id] = new_reader
        return new_reader

    # 1. Copy Ramjet hovering AnimationClips
    print("    [+] Transferring Ramjet hovering AnimationClips...")
    for pid in [-3269626749068485419, 2572480381784284055]:
        import_object_to_tc(r_sf.objects[pid], class_id=74)

    # 2. Copy Tantrum Bullet, Flame Particle, and Materials
    print("    [+] Transferring Tantrum Bullet & Flame Projectile objects...")
    tantrum_items = [
        (25807113867976956, 1, None),             # projectile_tantrum_bullet (GameObject)
        (5713893038463575376, 4, None),           # Transform
        (334539977581653716, 114, "Projectile"),  # Projectile
        (8324526433898494969, 114, "MoveSet"),    # MoveSet
        (2388614115523338286, 114, "PrefabLib"),  # PrefabLib
        (6848476052244691949, 114, "MoveSequencer"), # MoveSequencer
        (9046032664050696218, 1, None),           # fx_p_tantrum_flame_projectile (GameObject)
        (-4014873154244582342, 4, None),          # Transform
        (2451089123004433142, 198, None),         # ParticleSystem (flame root)
        (8876437021037049184, 199, None),         # ParticleSystemRenderer
        (4111356551118868481, 1, None),           # smoke (GameObject)
        (6876391030932467905, 4, None),           # Transform
        (5569254531370579145, 198, None),         # ParticleSystem (smoke)
        (-2121895461520731965, 199, None),        # ParticleSystemRenderer (smoke)
        (1397324567582396375, 21, None),          # fx_m_tantrum_projectile_a (Material)
        (-2064251451381054372, 21, None),         # fx_m_tantrum_smoke_b (Material)
        (-7910150966540381853, 21, None),         # fx_m_tantrum_fireball (Material)
    ]

    for pid, cid, sname in tantrum_items:
        import_object_to_tc(t_sf.objects[pid], class_id=cid, script_name=sname)

    # 2.5 Copy Starscream Special Bullet (for S2 gunfire)
    print("    [+] Transferring Starscream Special Bullet objects (for S2 gunfire)...")
    special_bullet_items = [
        (-17672961250916481, 1, None),             # projectile_special_bullet (GameObject)
        (5114465074849567931, 4, None),            # Transform
        (6911381496922764941, 114, "Projectile"),  # MoveToPlayOnFire
        (4570473581685628392, 114, "MoveSet"),     # _moves
        (6656473622135015614, 114, "PrefabLib"),   # PrefabList
        (-2567301930229054027, 114, "MoveSequencer"), # CombatEntity
    ]
    for pid, cid, sname in special_bullet_items:
        import_object_to_tc(c_sf.objects[pid], class_id=cid, script_name=sname)

    # Remap dependencies for both projectiles
    tb_moves_reader = tc_sf.objects[8324526433898494969]
    tb_moves_tree = tb_moves_reader.read_typetree()
    for m in tb_moves_tree.get("_moves", []):
        if m.get("_asset", {}).get("m_FileID") == 3:
            m["_asset"]["m_FileID"] = 6
    tb_moves_reader.save_typetree(tb_moves_tree)

    tb_plib_reader = tc_sf.objects[2388614115523338286]
    tb_plib_tree = tb_plib_reader.read_typetree()
    for item in tb_plib_tree.get("PrefabList", []):
        if item.get("Prefab", {}).get("m_FileID") == 6:
            item["Prefab"]["m_FileID"] = 5
    tb_plib_reader.save_typetree(tb_plib_tree)

    sb_moves_reader = tc_sf.objects[4570473581685628392]
    sb_moves_tree = sb_moves_reader.read_typetree()
    for m in sb_moves_tree.get("_moves", []):
        if m.get("_asset", {}).get("m_FileID") == 5:
            m["_asset"]["m_FileID"] = 6
    sb_moves_reader.save_typetree(sb_moves_tree)

    sb_plib_reader = tc_sf.objects[6656473622135015614]
    sb_plib_tree = sb_plib_reader.read_typetree()
    for item in sb_plib_tree.get("PrefabList", []):
        if item.get("Prefab", {}).get("m_FileID") == 7:
            item["Prefab"]["m_FileID"] = 5
    sb_plib_reader.save_typetree(sb_plib_tree)

    # 3. Retint Tantrum Materials & Particles to Ghost Blue
    print("    [+] Retinting flame materials and particles to Ghost Blue (#00E5FF)...")
    mat_a = tc_sf.objects[1397324567582396375]
    mat_a_tree = mat_a.read_typetree()
    sp = mat_a_tree.get("m_SavedProperties", {})
    new_colors = []
    for c in sp.get("m_Colors", []):
        if c[0] == "_emissive_intensity_col":
            new_colors.append((c[0], {"r": 0.05, "g": 0.85, "b": 1.0, "a": 1.0}))
        else:
            new_colors.append(c)
    sp["m_Colors"] = new_colors
    mat_a_tree["m_SavedProperties"] = sp
    mat_a.save_typetree(mat_a_tree)

    mat_b = tc_sf.objects[-2064251451381054372]
    mat_b_tree = mat_b.read_typetree()
    sp_b = mat_b_tree.get("m_SavedProperties", {})
    new_colors_b = []
    for c in sp_b.get("m_Colors", []):
        if c[0] == "_TintColor":
            new_colors_b.append((c[0], {"r": 0.2, "g": 0.8, "b": 1.0, "a": 0.45}))
        elif c[0] == "_emissive_intensity_col":
            new_colors_b.append((c[0], {"r": 0.1, "g": 0.8, "b": 1.0, "a": 1.0}))
        else:
            new_colors_b.append(c)
    sp_b["m_Colors"] = new_colors_b
    mat_b_tree["m_SavedProperties"] = sp_b
    mat_b.save_typetree(mat_b_tree)

    ps_flame = tc_sf.objects[2451089123004433142]
    ps_tree = ps_flame.read_typetree()
    if "ColorModule" in ps_tree:
        grad = ps_tree["ColorModule"]["gradient"]["maxGradient"]
        grad["key0"] = {"r": 0.75, "g": 0.95, "b": 1.0, "a": 1.0}
        grad["key1"] = {"r": 0.05, "g": 0.75, "b": 1.0, "a": 0.85}
        grad["key2"] = {"r": 0.10, "g": 0.85, "b": 1.0, "a": 0.0}
        grad["key3"] = {"r": 0.10, "g": 0.85, "b": 1.0, "a": 0.0}
        grad["key4"] = {"r": 0.00, "g": 0.40, "b": 1.0, "a": 0.0}
        ps_tree["ColorModule"]["gradient"]["maxGradient"] = grad
        ps_flame.save_typetree(ps_tree)

    # 4. Synthesize Ghost Starscream Textures directly from authentic Starscream assets
    print("    [+] Synthesizing authentic Ghost Starscream textures (Spectral Cyan Plasma, Blinding Chest Flare, B/A Emissive)...")
    sc_main_img = None
    sc_tform_img = None
    sc_raoe_img = None
    sc_mesh_obj = None

    for obj in c_env.objects:
        if obj.type.name == "Texture2D":
            name = obj.read().m_Name
            if name == "cha_starscream_gs_leader2015_main_a":
                sc_main_img = obj.read().image
            elif obj.path_id == 6557019140021768822:
                sc_tform_img = obj.read().image
            elif obj.path_id == -9219339549118775314:
                sc_raoe_img = obj.read().image
        elif obj.type.name == "Mesh" and obj.read().m_Name == "cha_starscream_gs_leader2015_00":
            sc_mesh_obj = obj.read().export()

    # Extract 3D UV masks for chest flare, surrounding glow, and leg fade
    lines = sc_mesh_obj.splitlines()
    verts, vts, faces_0, faces_1 = [], [], [], []
    cur_g = ""
    for l in lines:
        if l.startswith("v "):
            verts.append([float(x) for x in l.split()[1:4]])
        elif l.startswith("vt "):
            vts.append([float(x) for x in l.split()[1:3]])
        elif l.startswith("g "):
            cur_g = l.split()[1]
        elif l.startswith("f "):
            p = l.split()[1:]
            fdata = []
            for x in p:
                sub = x.split("/")
                vi = int(sub[0]) - 1
                vti = int(sub[1]) - 1 if len(sub) > 1 and sub[1] else -1
                fdata.append((vi, vti))
            if cur_g == "cha_starscream_gs_leader2015_00_0":
                faces_0.append(fdata)
            elif cur_g == "cha_starscream_gs_leader2015_00_1":
                faces_1.append(fdata)

    verts = np.array(verts)
    vts = np.array(vts)
    w, h = 1024, 1024

    mask_chest_flare = Image.new("L", (w, h), 0)
    mask_chest_outer = Image.new("L", (w, h), 0)
    mask_legs_fade = Image.new("L", (w, h), 0)

    draw_chest_flare = ImageDraw.Draw(mask_chest_flare)
    draw_chest_outer = ImageDraw.Draw(mask_chest_outer)
    draw_legs_fade = ImageDraw.Draw(mask_legs_fade)

    for f in faces_0:
        if len(f) < 3:
            continue
        f_vis = [vi for vi, _ in f]
        f_vtis = [vti for _, vti in f if vti >= 0]
        if len(f_vtis) < 3:
            continue
        fv = verts[f_vis]
        fvt = vts[f_vtis]
        avg_y = fv[:, 1].mean()
        avg_x = fv[:, 0].mean()
        avg_z = fv[:, 2].mean()
        pts = [(int(np.clip(u * w, 0, w - 1)), int(np.clip((1.0 - v) * h, 0, h - 1))) for u, v in fvt]

        # Center chest spark flare: Y in [7.2, 8.4], abs(X) <= 0.45, Z >= 0.35
        if 7.2 <= avg_y <= 8.4 and abs(avg_x) <= 0.45 and avg_z >= 0.35:
            draw_chest_flare.polygon(pts, fill=255)
        # Surrounding chest glow: Y in [6.5, 9.0], abs(X) <= 1.2, Z >= 0.15
        elif 6.5 <= avg_y <= 9.0 and abs(avg_x) <= 1.2 and avg_z >= 0.15:
            draw_chest_outer.polygon(pts, fill=200)

        # Leg fade: Y <= 3.8
        if avg_y <= 3.8:
            fade_val = int(np.clip((3.8 - avg_y) / 3.8 * 255.0, 0, 255))
            draw_legs_fade.polygon(pts, fill=fade_val)

    m_arr = np.array(sc_main_img.convert("RGBA"), dtype=np.float32)
    mr, mg, mb, ma = m_arr[..., 0], m_arr[..., 1], m_arr[..., 2], m_arr[..., 3]
    lum = (mr * 0.299 + mg * 0.587 + mb * 0.114) / 255.0

    # 4a. Base Spectral Cyan Armor (Toned down, distinct mechanical structure)
    ghost_r = np.clip(lum * 18.0 + 6.0, 0, 255)
    ghost_g = np.clip(lum * 110.0 + 60.0, 0, 255)  # 60 ~ 170
    ghost_b = np.clip(lum * 100.0 + 100.0, 0, 255) # 100 ~ 200

    # 4b. Chest Spark (Clean white-cyan core without blinding whole body)
    m_flare = np.array(mask_chest_flare.filter(ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255.0
    ghost_r = ghost_r * (1.0 - m_flare) + 210.0 * m_flare
    ghost_g = ghost_g * (1.0 - m_flare) + 255.0 * m_flare
    ghost_b = ghost_b * (1.0 - m_flare) + 255.0 * m_flare

    # 4c. Eyes: FIERY NEON RED (User Request: "然后眼睛调成红光")
    mask_eyes_3d = Image.new("L", (w, h), 0)
    draw_eyes_3d = ImageDraw.Draw(mask_eyes_3d)
    for f in faces_0:
        if len(f) < 3: continue
        vis = [v[0] for v in f]
        vtis = [v[1] for v in f if v[1] >= 0]
        if len(vtis) < 3: continue
        fv = verts[vis]
        fvt = vts[vtis]
        avg_y = fv[:, 1].mean()
        avg_x = fv[:, 0].mean()
        avg_z = fv[:, 2].mean()
        pts = [(int(np.clip(u * w, 0, w - 1)), int(np.clip((1.0 - v) * h, 0, h - 1))) for u, v in fvt]
        if 9.15 <= avg_y <= 9.55 and abs(avg_x) <= 0.15 and avg_z >= 0.38:
            draw_eyes_3d.polygon(pts, fill=255)

    yy, xx = np.mgrid[0:h, 0:w]
    m_eyes_2d = (xx >= 352) & (xx <= 412) & (yy >= 262) & (yy <= 312) & ((mr > 110) | (mb > 140))
    m_eyes_total = (np.array(mask_eyes_3d) > 50) | m_eyes_2d

    # Red eye glow corona
    m_eye_glow = np.array(Image.fromarray((m_eyes_total * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255.0

    # Dark faceplate to make red eyes dramatically pop
    m_faceplate = (xx >= 340) & (xx <= 425) & (yy >= 245) & (yy <= 335) & (~m_eyes_total)
    ghost_r[m_faceplate] = 10.0
    ghost_g[m_faceplate] = 30.0
    ghost_b[m_faceplate] = 45.0

    # Apply vivid red to eyes and corona
    ghost_r = ghost_r * (1.0 - m_eye_glow) + 255.0 * m_eye_glow
    ghost_g = ghost_g * (1.0 - m_eye_glow) + 5.0 * m_eye_glow
    ghost_b = ghost_b * (1.0 - m_eye_glow) + 5.0 * m_eye_glow

    # Hard core pure scarlet red eyes
    ghost_r[m_eyes_total] = 255.0
    ghost_g[m_eyes_total] = 0.0
    ghost_b[m_eyes_total] = 0.0

    # Decepticon insignia: vivid crimson red
    is_insignia = (mr > 130) & (mg < 60) & (mb > 130) & (yy > 500) & (yy < 660) & (xx > 650) & (xx < 800)
    ghost_r[is_insignia] = 255.0
    ghost_g[is_insignia] = 10.0
    ghost_b[is_insignia] = 10.0

    # 4d. Leg Ghost Dissolve:
    m_legs = np.array(mask_legs_fade, dtype=np.float32) / 255.0
    leg_edges = np.array(mask_legs_fade.filter(ImageFilter.FIND_EDGES)) > 20

    fade_strength = np.clip(m_legs ** 0.8, 0.0, 0.88)
    ghost_r = ghost_r * (1.0 - fade_strength) + 6.0 * fade_strength
    ghost_g = ghost_g * (1.0 - fade_strength) + 20.0 * fade_strength
    ghost_b = ghost_b * (1.0 - fade_strength) + 32.0 * fade_strength

    # Retain glowing wireframe edge on legs
    ghost_r = np.where(leg_edges & (m_legs > 0.1), 0.0, ghost_r)
    ghost_g = np.where(leg_edges & (m_legs > 0.1), 220.0, ghost_g)
    ghost_b = np.where(leg_edges & (m_legs > 0.1), 245.0, ghost_b)

    ghost_a = np.clip(255.0 * (1.0 - fade_strength * 0.90), 20.0, 255.0)

    final_main_albedo = Image.fromarray(np.stack([np.clip(ghost_r, 0, 255), np.clip(ghost_g, 0, 255), np.clip(ghost_b, 0, 255), ghost_a], axis=-1).astype(np.uint8))

    # 4e. Synthesize Vehicle (Tform Misc / Wings / Cockpit) Albedo
    tform_arr = np.array(sc_tform_img.convert("RGBA"), dtype=np.float32)
    tr, tg, tb, ta = tform_arr[..., 0], tform_arr[..., 1], tform_arr[..., 2], tform_arr[..., 3]
    tlum = (tr * 0.299 + tg * 0.587 + tb * 0.114) / 255.0

    # Spectral Cyan Wings & vehicle body (Toned down)
    t_ghost_r = np.clip(tlum * 18.0 + 6.0, 0, 255)
    t_ghost_g = np.clip(tlum * 110.0 + 60.0, 0, 255)
    t_ghost_b = np.clip(tlum * 100.0 + 100.0, 0, 255)

    # Cockpit canopy & intakes -> White-Cyan Blazing Energy Core (spark)
    is_cockpit = (tr > 170) & (tg > 100) & (tb < 80)
    is_cockpit_dilated = np.array(Image.fromarray((is_cockpit * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))) / 255.0

    t_ghost_r = t_ghost_r * (1.0 - is_cockpit_dilated) + 210.0 * is_cockpit_dilated
    t_ghost_g = t_ghost_g * (1.0 - is_cockpit_dilated) + 255.0 * is_cockpit_dilated
    t_ghost_b = t_ghost_b * (1.0 - is_cockpit_dilated) + 255.0 * is_cockpit_dilated

    final_tform_albedo = Image.fromarray(np.stack([t_ghost_r, t_ghost_g, t_ghost_b, ta], axis=-1).astype(np.uint8))

    # 4f. Synthesize Weapons Albedo
    tc_wpns = None
    for obj in tc_env.objects:
        if obj.type.name == "Texture2D" and obj.read().m_Name == "cha_thundercracker_gs_leader2015_wpns_a":
            tc_wpns = obj.read().image
            break
    w_arr = np.array(tc_wpns.convert("RGBA"), dtype=np.float32)
    wr, wg, wb, wa = w_arr[..., 0], w_arr[..., 1], w_arr[..., 2], w_arr[..., 3]
    wlum = (wr * 0.299 + wg * 0.587 + wb * 0.114) / 255.0
    w_r = np.clip(wlum * 18.0 + 6.0, 0, 255)
    w_g = np.clip(wlum * 110.0 + 60.0, 0, 255)
    w_b = np.clip(wlum * 100.0 + 100.0, 0, 255)
    final_wpns_albedo = Image.fromarray(np.stack([w_r, w_g, w_b, wa], axis=-1).astype(np.uint8))

    # 4g. Synthesize Main RAOE Texture (512x512, RGBA32)
    # Toned down emissive (55 base, not 245) to prevent overbright whiteout!
    raoe_r = np.full((512, 512), 15, dtype=np.uint8)   # Mirror roughness
    raoe_g = np.full((512, 512), 240, dtype=np.uint8)  # Chrome metallic

    # Base body emissive: 55 (subtle, ethereal ghost luminescence)
    raoe_b = np.full((512, 512), 55, dtype=np.uint8)
    raoe_a = np.full((512, 512), 65, dtype=np.uint8)

    legs_512 = np.array(mask_legs_fade.resize((512, 512)), dtype=np.float32) / 255.0
    fade_512 = np.clip(legs_512 ** 0.8, 0.0, 0.88)
    raoe_b = np.clip(55.0 * (1.0 - fade_512), 5.0, 255.0).astype(np.uint8)
    raoe_a = np.clip(65.0 * (1.0 - fade_512), 5.0, 255.0).astype(np.uint8)

    # Chest spark: 200 (bright glowing energy core)
    flare_512 = np.array(mask_chest_flare.resize((512, 512)), dtype=np.float32) > 50
    raoe_b[flare_512] = 200
    raoe_a[flare_512] = 220

    # EYES: Zero out cyan emissive on eyes so red optics shine completely pure!
    eyes_512 = np.array(Image.fromarray((m_eyes_total * 255).astype(np.uint8)).resize((512, 512))) > 30
    raoe_b[eyes_512] = 0
    raoe_a[eyes_512] = 0

    final_raoe = Image.fromarray(np.stack([raoe_r, raoe_g, raoe_b, raoe_a], axis=-1))

    # 4h. Synthesize Weapons RAOE Texture (256x256, RGBA32)
    w_raoe_r = np.full((256, 256), 15, dtype=np.uint8)
    w_raoe_g = np.full((256, 256), 240, dtype=np.uint8)
    w_raoe_b = np.full((256, 256), 55, dtype=np.uint8)
    w_raoe_a = np.full((256, 256), 65, dtype=np.uint8)
    final_wpns_raoe = Image.fromarray(np.stack([w_raoe_r, w_raoe_g, w_raoe_b, w_raoe_a], axis=-1))

    # Inject textures into target bundle with RGBA32 format (Format 4)
    albedo_reader = tc_sf.objects[-7847136875210576777]
    albedo_data = albedo_reader.read()
    albedo_data.m_TextureFormat = 4 # RGBA32 (preserves alpha channel!)
    albedo_data.image = final_main_albedo
    albedo_data.save()

    tform_reader = tc_sf.objects[-5777190166173245582]
    tform_data = tform_reader.read()
    tform_data.m_TextureFormat = 4 # RGBA32
    tform_data.image = final_tform_albedo
    tform_data.save()

    raoe_reader = tc_sf.objects[110708219653106618]
    raoe_data = raoe_reader.read()
    raoe_data.m_TextureFormat = 4 # RGBA32
    raoe_data.image = final_raoe
    raoe_data.save()

    wpns_reader = tc_sf.objects[-7503008434217827270]
    wpns_data = wpns_reader.read()
    wpns_data.m_TextureFormat = 4 # RGBA32
    wpns_data.image = final_wpns_albedo
    wpns_data.save()

    wpns_raoe_reader = tc_sf.objects[8424737046714802559]
    wpns_raoe_data = wpns_raoe_reader.read()
    wpns_raoe_data.m_TextureFormat = 4 # RGBA32
    wpns_raoe_data.image = final_wpns_raoe
    wpns_raoe_data.save()

    print("    [+] Successfully injected balanced Ghost textures with red eyes and toned-down B+A Emissive RAOE!")

    # 5. Configure Ghost Materials (Toned-down Ethereal Bloom + Ghost Transparency)
    print("    [+] Configuring Ghost PBR Material properties on ALL character materials...")
    body_mat_pids = [
        -6484692870300716619, # 71FF6BF5D6A75FD9C95F8E24782D25AAC5D9A272 (main albedo)
        3730148394312270616,  # 5A4E0F29019DE7EB4A51394A0F22A3565E1E76B1 (tform misc)
        823767062428791324,   # 81A21DEE09F1FB023610228E9C9C3EA7B20A110C (cockpit / weapons)
        5728535627619097273,  # 9674AFC81016CDA7FCCF94995D908A991DECE420 (wings)
    ]
    for b_pid in body_mat_pids:
        b_mat = tc_sf.objects.get(b_pid)
        if not b_mat:
            continue
        b_tree = b_mat.read_typetree()
        sp = b_tree.get("m_SavedProperties", {})

        new_colors = []
        for c in sp.get("m_Colors", []):
            if c[0] == "_emissive_intensity_col":
                new_colors.append((c[0], {"r": 0.05, "g": 0.90, "b": 1.0, "a": 1.0}))
            else:
                new_colors.append(c)
        if not any(c[0] == "_emissive_intensity_col" for c in new_colors):
            new_colors.append(("_emissive_intensity_col", {"r": 0.05, "g": 0.90, "b": 1.0, "a": 1.0}))
        sp["m_Colors"] = new_colors

        float_updates = {
            "_emissive_overbright_range": 28.0,
            "_emissive_range": 1.0,
            "_emissive_ramp_range": 0.7,
            "_emissive_pulse_intensity_range": 0.25,
            "_emissive_pulse_time_range": 1.8,
            "_clearcoat_reflectance_range": 0.85,
            "_reflectance": 0.15,
            "_Mode": 3.0,
            "_SrcBlend": 1.0,
            "_DstBlend": 10.0,
            "_ZWrite": 0.0,
        }
        new_floats = []
        for f in sp.get("m_Floats", []):
            if f[0] in float_updates:
                new_floats.append((f[0], float_updates.pop(f[0])))
            else:
                new_floats.append(f)
        for k, v in float_updates.items():
            new_floats.append((k, v))
        sp["m_Floats"] = new_floats

        b_tree["m_SavedProperties"] = sp
        b_tree["m_CustomRenderQueue"] = 3000
        b_tree["m_ShaderKeywords"] = "EB_SECOND_DIRECTIONAL_LIGHT_ON _AO_TEX _BASE_TEX _EMISSIVE_TEX _METALLIC_TEX _MODE_CLEARCOAT _NORMAL_TEX _ROUGHNESS_TEX _ALPHAPREMULTIPLY_ON"
        b_tree["stringTagMap"] = [("RenderType", "Transparent")]
        replace_str_in_tree(b_tree, old_cab, new_cab)
        b_mat.save_typetree(b_tree)

    # 6. Configure AnimatorOverrideController (AOC)
    print("    [+] Re-wiring AnimatorOverrideController for hovering & melee combat...")
    aoc_reader = None
    for o in tc_sf.objects.values():
        if o.type.name == "AnimatorOverrideController" and "fight" in getattr(o.read(), "m_Name", "").lower():
            aoc_reader = o
            break

    aoc_tree = aoc_reader.read_typetree()
    clips = aoc_tree.get("m_Clips", [])

    # Hover Idle & Locorun (from Ramjet local clips, FileID=0)
    clips[0]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -3269626749068485419}  # Ramjet_G1_CombatIdle
    clips[1]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 2572480381784284055}   # Ramjet_locorun

    # Hover dodge / dash / sidestep (Waspinator procedural rig, FileID=3)
    clips[6]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 7332880014435233504}   # waspinator_bw_locoDodge
    clips[8]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -5773161447144622359}  # waspinator_bw_locoSidestep_left
    clips[21]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -671649575409783368}  # waspinator_bw_locoSidestep_right
    clips[13]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -3084339264270582057} # waspinator_bw_locoDash_Start
    clips[9]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 1228286978232073708}   # waspinator_locoDash_Loop

    # Melee combo (Waspinator brawler chain, FileID=3)
    clips[2]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 7015914262721624539}   # brawler_waspinator_attackLight_01_jab
    clips[3]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 4728921514059308593}   # brawler_waspinator_attackLight_02_jab
    clips[41]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -3992976558540121099} # brawler_waspinator_attackLight_03_uppercut
    clips[43]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 8942877049245720107}  # brawler_waspinator_attackLight_04_frontkick
    clips[42]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -8351645349661784384} # brawler2_waspinator_attackMedium_01_uppercut
    clips[44]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 9045806334692434763}  # brawler2_waspinator_attackMedium_02_sidekick
    clips[58]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -8287216037977883126} # Ramjet_Normal_attackHeavy

    # Specials:
    # S1: Sideswipe S1 (sideswipe_attackSpecial_01, FileID=3)
    clips[4]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -1258062485005751563}
    # S2: Starscream S1 (starscream_gs_attackSpecial_01_gunfire, local FileID=0)
    clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 365167208182465683}
    # S3: Starscream S3 (starscream_g1_attackSpecial_03, FileID=3)
    clips[31]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": -2847551444379563947}
    clips[32]["m_OverrideClip"] = {"m_FileID": 3, "m_PathID": 5028105688585685399}

    aoc_tree["m_Clips"] = clips
    aoc_reader.save_typetree(aoc_tree)

    # 7. Configure MoveSet on character root
    print("    [+] Re-wiring MoveSet actions and hitboxes...")
    root_moveset = None
    root_prefablib = None
    for o in tc_sf.objects.values():
        if o.type.name == "MonoBehaviour":
            s_name = getattr(o.read(), "m_Script", type('',(),{'read':lambda s:type('',(),{'m_Name':''})()})).read().m_Name
            if s_name == "MoveSet":
                tree = o.read_typetree()
                if len(tree.get("_moves", [])) >= 40:
                    root_moveset = o
            elif s_name == "PrefabLib":
                tree = o.read_typetree()
                if len(tree.get("PrefabList", [])) >= 10:
                    root_prefablib = o

    ms_tree = root_moveset.read_typetree()
    moves = ms_tree.get("_moves", [])
    for m in moves:
        st = m.get("_animStateName", "")
        # Lights 01..04
        if st == "Base.LightAttack01":
            m["_name"] = "move_ramjet_attack_light_01"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 7359816885264639258}
        elif st == "Base.LightAttack02":
            m["_name"] = "move_ramjet_attack_light_02"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 295392445694360506}
        elif st == "Base.LightAttack03":
            m["_name"] = "move_ramjet_attack_light_03"
            m["_asset"] = {"m_FileID": 6, "m_PathID": -8204220784975141094}
        elif st == "Base.LightAttack04":
            m["_name"] = "move_ramjet_attack_light_04"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 1557775265196915232}
        # Mediums 01..02
        elif st == "Base.MediumAttack01":
            m["_name"] = "move_ramjet_attack_medium_01"
            m["_asset"] = {"m_FileID": 6, "m_PathID": -8717739521390833225}
        elif st == "Base.MediumAttack02":
            m["_name"] = "move_ramjet_attack_medium_02"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 425225458416179913}
        # Heavy Attack
        elif st == "Base.HeavyAttack":
            m["_name"] = "move_heavy_ramjet_donut"
            m["_asset"] = {"m_FileID": 6, "m_PathID": -8528702938335562906}
        # Dash & Run
        elif st == "Base.DashStart":
            m["_name"] = "move_ramjet_dash"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 2391443251058531702}
        elif st == "Base.Run":
            m["_name"] = "move_ramjet_run"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 7408579482114667044}
        # S1: Sideswipe S1
        elif st == "Base.SpecialAttack01":
            m["_name"] = "move_sideswipe_special_01"
            m["_asset"] = {"m_FileID": 6, "m_PathID": -8581691460356634301}
        # S2: Starscream S1
        elif st == "Base.SpecialAttack02":
            m["_name"] = "move_starscream_special_01"
            m["_asset"] = {"m_FileID": 6, "m_PathID": 9089968971165329940}
        # Ranged Attacks: Ghost Bursts
        elif st == "Base.RangedAttack01":
            m["_name"] = "move_attackRanged_stars_ghost_burst_01"
            m["_asset"] = {"m_FileID": 6, "m_PathID": GHOST_BURST_01_PID}
        elif st == "Base.RangedAttack02":
            m["_name"] = "move_attackRanged_stars_ghost_burst_02"
            m["_asset"] = {"m_FileID": 6, "m_PathID": GHOST_BURST_02_PID}
        elif st == "Base.RangedAttack03":
            m["_name"] = "move_attackRanged_stars_ghost_burst_03"
            m["_asset"] = {"m_FileID": 6, "m_PathID": GHOST_BURST_03_PID}

    ms_tree["_moves"] = moves
    root_moveset.save_typetree(ms_tree)

    # 8. Configure PrefabLib: inject projectile_tantrum_bullet, projectile_special_bullet, and flame particle
    print("    [+] Registering projectiles in root PrefabLib...")
    plib_tree = root_prefablib.read_typetree()
    plist = plib_tree.get("PrefabList", [])
    
    needed_prefabs = [
        (25807113867976956, 4),   # projectile_tantrum_bullet
        (-17672961250916481, 4),  # projectile_special_bullet
        (9046032664050696218, 4), # fx_p_tantrum_flame_projectile
    ]
    present_pids = set(item.get("Prefab", {}).get("m_PathID") for item in plist)
    for req_pid, req_amt in needed_prefabs:
        if req_pid not in present_pids:
            plist.append({"Prefab": {"m_FileID": 0, "m_PathID": req_pid}, "Amount": req_amt})
            present_pids.add(req_pid)
    plib_tree["PrefabList"] = plist
    root_prefablib.save_typetree(plib_tree)

    # Rename GameObjects and Mesh objects to Starscream
    for o in tc_sf.objects.values():
        if o.type.name == "GameObject":
            tree = o.read_typetree()
            gname = tree.get("m_Name", "")
            if "thundercracker" in gname.lower():
                tree["m_Name"] = gname.replace("Thundercracker_GS_leader2015", "Starscream_Ghost_GS").replace("thundercracker", "starscream")
                o.save_typetree(tree)
        elif o.type.name == "Mesh":
            tree = o.read_typetree()
            mname = tree.get("m_Name", "")
            if "thundercracker" in mname.lower():
                tree["m_Name"] = mname.replace("thundercracker", "starscream")
                o.save_typetree(tree)

    # Apply CAB replacement to already modified trees
    replace_str_in_tree(aoc_tree, old_cab, new_cab)
    aoc_reader.save_typetree(aoc_tree)

    replace_str_in_tree(ms_tree, old_cab, new_cab)
    root_moveset.save_typetree(ms_tree)

    replace_str_in_tree(plib_tree, old_cab, new_cab)
    root_prefablib.save_typetree(plib_tree)

    replace_str_in_tree(tb_moves_tree, old_cab, new_cab)
    tb_moves_reader.save_typetree(tb_moves_tree)
    replace_str_in_tree(tb_plib_tree, old_cab, new_cab)
    tb_plib_reader.save_typetree(tb_plib_tree)

    replace_str_in_tree(sb_moves_tree, old_cab, new_cab)
    sb_moves_reader.save_typetree(sb_moves_tree)
    replace_str_in_tree(sb_plib_tree, old_cab, new_cab)
    sb_plib_reader.save_typetree(sb_plib_tree)

    modified_pids = {
        aoc_reader.path_id,
        root_moveset.path_id,
        root_prefablib.path_id,
        albedo_reader.path_id,
        tform_reader.path_id,
        raoe_reader.path_id,
        wpns_reader.path_id,
        wpns_raoe_reader.path_id,
        mat_a.path_id,
        mat_b.path_id,
        ps_flame.path_id,
        tb_moves_reader.path_id,
        tb_plib_reader.path_id,
        sb_moves_reader.path_id,
        sb_plib_reader.path_id,
    }
    modified_pids.update(body_mat_pids)

    # 9. Isolate CAB and Rename AssetBundle
    print(f"    [+] Performing CAB isolation: {old_cab} -> {new_cab}...")
    for o in tc_sf.objects.values():
        if o.path_id in modified_pids:
            continue
        if o.type.name == "AssetBundle":
            tree = o.read_typetree()
            tree["m_Name"] = "data/starscream_ghost_gs_odr/starscream_ghost_gs.assetbundle"
            tree["m_AssetBundleName"] = "data/starscream_ghost_gs_odr/starscream_ghost_gs.assetbundle"

            orig_table = tree.get("m_PreloadTable", [])
            injected_pids = [
                # Ramjet clips
                -3269626749068485419, 2572480381784284055,
                # Tantrum bullet & flame
                25807113867976956, 5713893038463575376, 334539977581653716, 8324526433898494969, 2388614115523338286, 6848476052244691949,
                9046032664050696218, -4014873154244582342, 2451089123004433142, 8876437021037049184, 4111356551118868481, 6876391030932467905,
                5569254531370579145, -2121895461520731965, 1397324567582396375, -2064251451381054372, -7910150966540381853,
                # Starscream special bullet
                -17672961250916481, 5114465074849567931, 6911381496922764941, 4570473581685628392, 6656473622135015614, -2567301930229054027
            ]
            new_entries = [{"m_FileID": 0, "m_PathID": pid} for pid in injected_pids]
            insert_idx = 1355
            merged_table = orig_table[:insert_idx] + new_entries + orig_table[insert_idx:]
            tree["m_PreloadTable"] = merged_table

            new_container = []
            for k, v in tree.get("m_Container", []):
                new_k = k.replace("thundercracker_gs_leader2015", "starscream_ghost_gs")
                entry_info = dict(v)
                if "starscream_ghost_gs.prefab" in new_k and "_lw.prefab" not in new_k:
                    entry_info["preloadSize"] = entry_info.get("preloadSize", 1355) + len(injected_pids)
                elif "_lw.prefab" in new_k:
                    entry_info["preloadIndex"] = entry_info.get("preloadIndex", 1355) + len(injected_pids)
                new_container.append((new_k, entry_info))
            tree["m_Container"] = new_container
            replace_str_in_tree(tree, old_cab, new_cab)
            o.save_typetree(tree)
        elif o.type.name == "GameObject":
            tree = o.read_typetree()
            gname = tree.get("m_Name", "")
            if "thundercracker_gs_leader2015" in gname.lower():
                tree["m_Name"] = gname.replace("Thundercracker_GS_leader2015", "Starscream_Ghost_GS").replace("thundercracker_gs_leader2015", "starscream_ghost_gs")
            replace_str_in_tree(tree, old_cab, new_cab)
            o.save_typetree(tree)
        elif o.type.name in ["MonoBehaviour", "Material", "Texture2D", "Mesh"]:
            try:
                tree = o.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                o.save_typetree(tree)
            except Exception:
                pass

    new_files = {}
    for subfname, subf in tc_bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf

    tc_bf.files = new_files
    tc_bf.version = 7
    tc_bf.version_engine = "2020.3.31f1"
    tc_bf.version_player = "5.x.x"

    saved_bytes = tc_bf.save(packer="lz4")
    out_bundle = OUT_DIR / "starscream_ghost_gs.assetbundle"
    out_bundle.write_bytes(saved_bytes)
    print(f"[+] Successfully generated {out_bundle} ({len(saved_bytes)} bytes)")


def main():
    setup_portraits()
    patch_moves_bundle()
    generate_ghost_starscream_bundle()
    print("[*] All Ghost Starscream assets generated successfully!")

if __name__ == "__main__":
    main()
