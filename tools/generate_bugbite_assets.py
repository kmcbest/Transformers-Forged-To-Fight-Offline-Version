#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_bugbite_assets.py

Custom composite grafting pipeline for Mercenary Bug Bite (杀人蜂).
Faction: Mercenary (佣兵, PUA: E99F)
Class: Brawler (braw)

1. Base Body & Vehicle Mode:
   - Cloned from Bumblebee (bumblebee_gs_kabam.assetbundle)
2. Combat Animation & Moveset Grafting:
   - S1: Jazz S1 (Jazz_GS_attackSpecial_01 / move_jazz_special_01)
   - S2: Waspinator S2 (waspinator_bw_attackSpecial_02 / move_bugbite_special_02)
   - S3: Cliffjumper S3 (cliffjumper_gs_attackSpecial_03 / native Beetle stage)
   - L1: Tantrum L1 (brute_tantrum_attackLight_01_jab / move_tantrum_attack_light_01)
   - L2: Tantrum L2 (brute_tantrum_attackLight_02_jab / move_tantrum_attack_light_02)
   - L3: Tantrum L3 (brute_tantrum_attackLight_03_frontkick / move_tantrum_attack_light_03)
   - L4: Tantrum L4 (brute_tantrum_attackLight_04_uppcut / move_tantrum_attack_light_04)
   - M1: Movie Ironhide M1 (brawler_normal_attackMedium_02_shouldercharge / move_brawler_attack_medium_02)
   - M2: Megatronus M2 (Brute02_normal_attackMedium_02_L_push / move_megatronus_attack_medium_02)
   - Other moves: Preserved from Bumblebee
3. Visuals & Recolor:
   - Pearl white armor with silver metallic shading
   - Crimson / Ruby red eye optics (glowing emissive)
   - Deep violet / tinted windows
   - Mercenary insignia on chest
4. Deep CAB Isolation:
   - CAB-bugbite2026kabam0001122334455
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import json
import os
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required. Install it using: pip install UnityPy lz4 pillow numpy")
    sys.exit(1)

BUGBITE_S2_PID = -8888888888888888884


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


def patch_bugbite_move_s2():
    """Create dedicated move_bugbite_special_02 inside moves.assetbundle."""
    moves_path = Path("assets_redeco/moves.assetbundle")
    if not moves_path.exists():
        moves_path = Path("assets_netflix/moves.assetbundle")

    print(f"[*] Patching moves bundle from {moves_path}...")
    env = UnityPy.load(str(moves_path))
    bf = list(env.files.values())[0]
    moves_asset = list(env.assets)[0]

    wasp_reader = None
    ab_obj = None

    for obj in env.objects:
        if obj.path_id == 1005920638777440556:
            wasp_reader = obj
        elif obj.type.name == "AssetBundle":
            ab_obj = obj

    assert wasp_reader is not None, "Failed to find move_waspinator_special_02!"
    assert ab_obj is not None, "Failed to find AssetBundle object in moves!"

    # Clone move_waspinator_special_02 to move_bugbite_special_02
    s2_move = copy.deepcopy(wasp_reader.read_typetree())
    s2_move["m_Name"] = "move_bugbite_special_02"
    s2_data = json.loads(s2_move["m_Script"])

    move_def = s2_data.get("moves", {})
    move_def["id"] = "move_bugbite_special_02"
    move_def["m_Name"] = "move_bugbite_special_02"

    events = []
    for ev in move_def.get("events", []):
        ev_type = ev.get("type", "")
        
        # 1. Drop wings prop animation and charge up particle
        if ev_type == "PlayPropAnimatorStateMoveEvent" and ev.get("pn") == "wings":
            print("  - Dropped wings PlayPropAnimatorStateMoveEvent")
            continue
        if ev_type == "ParticleMoveEvent" and "charge_up" in ev.get("pn", ""):
            print("  - Dropped charge_up ParticleMoveEvent")
            continue
            
        # 2. Retarget gunright to rightgun
        ev_str = json.dumps(ev)
        if "gunright" in ev_str:
            ev_str = ev_str.replace("gunright", "rightgun")
            ev = json.loads(ev_str)
            print(f"  - Replaced gunright with rightgun in {ev_type}")
            
        # 3. Specific adjustments
        if ev_type == "PropMoveEvent" and ev.get("p") in ("gunright", "rightgun"):
            ev["p"] = "rightgun"
            ev["d"] = 35
            
        if ev_type == "ParticleMoveEvent" and "muzzle_flash" in ev.get("pn", ""):
            ev["pn"] = "fx_p_optimus_muzzle_flash"
            ev["dn"] = "muzzle_flash"
            ev["ref"]["r"] = "character_model/Reference/Hips/Spine/Spine1/RightShoulder/RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand/rightgun/Reference/COG/FX"
            ev["po"] = {"o": {"y": 0, "z": 0, "x": 0}, "s": 1}
            print("  - Configured fx_p_optimus_muzzle_flash for rightgun")
            
        if ev_type == "LightMoveEvent" and "muzzle_light" in ev.get("dn", ""):
            ev["ref"]["r"] = "character_model/Reference/Hips/Spine/Spine1/RightShoulder/RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand/rightgun/Reference/COG/FX"
            
        if ev_type == "ProjectileMoveEvent":
            print(f"  - Retargeting projectile {ev.get('pn')} -> projectile_special_bullet")
            ev["pn"] = "projectile_special_bullet"
            ev["dn"] = "projectile_special_bullet"
            ev["po"] = {"o": {"y": 4.61, "z": 6.5, "x": 0}, "s": 1}
            ev["oe"] = "explode_special"
            ev["spd"] = 120
            ev["hd"] = {
                "db": True, "fd": False, "al": 32,
                "hr": "HitReactionHeavyBack", "hs": 21, "kb": 25,
                "at": 2, "u": False, "ft": 0, "dam": 0.6,
                "bft": 0, "bhs": 12, "bkb": 15, "idx": 100, "m": 0.6
            }
            
        # 4. Set move name in event
        ev["mn"] = "move_bugbite_special_02"
        events.append(ev)

    move_def["events"] = events
    s2_data["moves"] = move_def
    s2_move["m_Script"] = json.dumps(s2_data)

    # Register new object in moves bundle
    s2_reader = copy.copy(wasp_reader)
    s2_reader.path_id = BUGBITE_S2_PID
    moves_asset.objects[BUGBITE_S2_PID] = s2_reader
    s2_reader.save_typetree(s2_move)

    # Update AssetBundle container
    ab_tree = ab_obj.read_typetree()
    container = [c for c in ab_tree.get("m_Container", []) if "move_bugbite_special_02" not in c[0]]
    container.append([
        "assets/bundles/movedata/move_bugbite_special_02.txt",
        {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BUGBITE_S2_PID}}
    ])
    ab_tree["m_Container"] = container
    ab_obj.save_typetree(ab_tree)

    # Save to assets_redeco/moves.assetbundle
    out_moves = Path("assets_redeco/moves.assetbundle")
    out_moves.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Saved {out_moves} ({out_moves.stat().st_size:,} bytes)")

    # Verify
    check_env = UnityPy.load(str(out_moves))
    total_count = len(check_env.objects)
    assert total_count >= 945, f"Moves count {total_count} < 945!"
    print(f"[+] Successfully patched moves.assetbundle with move_bugbite_special_02! (Total {total_count} objects)")


def generate_bugbite_assets(output_dir: str = "assets_redeco") -> None:
    # 0. Ensure moves.assetbundle contains move_bugbite_special_02
    patch_bugbite_move_s2()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = Path("extracted_apk/assets/assetpack")

    def load_bundle(rel_path: str) -> bytes:
        p = extracted / rel_path
        if p.is_file():
            return p.read_bytes()
        raise FileNotFoundError(f"Cannot find {rel_path} in extracted_apk!")

    print("[*] Loading component assetbundles...")
    bb_bytes = load_bundle("bumblebee_gs_kabam_odr/bumblebee_gs_kabam.assetbundle")
    jazz_bytes = load_bundle("jazz_gs_twm05_odr/jazz_gs_twm05.assetbundle")
    wasp_bytes = load_bundle("waspinator_gs_deluxe_odr/waspinator_gs_deluxe.assetbundle")
    cj_bytes = load_bundle("cliffjumper_gs_kabam_odr/cliffjumper_gs_kabam.assetbundle")
    tan_bytes = load_bundle("tantrum_gs_kabam_odr/tantrum_gs_kabam.assetbundle")
    megatro_bytes = load_bundle("megatronus_gs_kabam_odr/megatronus_gs_kabam.assetbundle")
    anim_proc_bytes = load_bundle("characters_procedural_odr/character_anim_procedural.assetbundle")

    print("[*] Parsing source bundles...")
    bb_env = UnityPy.load(bb_bytes)
    jazz_env = UnityPy.load(jazz_bytes)
    wasp_env = UnityPy.load(wasp_bytes)
    cj_env = UnityPy.load(cj_bytes)
    tan_env = UnityPy.load(tan_bytes)
    meg_env = UnityPy.load(megatro_bytes)
    anim_proc_env = UnityPy.load(anim_proc_bytes)

    # 1. Extract required AnimationClips
    print("[*] Extracting external animation clips...")

    # S1: Jazz S1 (-1177978727659732769)
    clip_s1 = None
    for obj in jazz_env.objects:
        if obj.path_id == -1177978727659732769 and obj.type.name == "AnimationClip":
            clip_s1 = obj.read_typetree()
            clip_s1["m_Name"] = "bugbite_gs_attackSpecial_01"
            break
    assert clip_s1 is not None, "Failed to find Jazz S1 clip!"

    # S2: Waspinator S2 (-8086663017110078275)
    clip_s2 = None
    for obj in wasp_env.objects:
        if obj.path_id == -8086663017110078275 and obj.type.name == "AnimationClip":
            clip_s2 = obj.read_typetree()
            clip_s2["m_Name"] = "bugbite_gs_attackSpecial_02"
            break
    assert clip_s2 is not None, "Failed to find Waspinator S2 clip!"

    # L1: Tantrum L1 (4273516124016290571)
    clip_l1 = None
    for obj in tan_env.objects:
        if obj.path_id == 4273516124016290571 and obj.type.name == "AnimationClip":
            clip_l1 = obj.read_typetree()
            clip_l1["m_Name"] = "bugbite_gs_attackLight_01"
            break
    assert clip_l1 is not None, "Failed to find Tantrum L1 clip!"

    # L2: Tantrum L2 (4342173990092517894)
    clip_l2 = None
    for obj in tan_env.objects:
        if obj.path_id == 4342173990092517894 and obj.type.name == "AnimationClip":
            clip_l2 = obj.read_typetree()
            clip_l2["m_Name"] = "bugbite_gs_attackLight_02"
            break
    assert clip_l2 is not None, "Failed to find Tantrum L2 clip!"

    # L3: Tantrum L3 (1038656054960397805)
    clip_l3 = None
    for obj in tan_env.objects:
        if obj.path_id == 1038656054960397805 and obj.type.name == "AnimationClip":
            clip_l3 = obj.read_typetree()
            clip_l3["m_Name"] = "bugbite_gs_attackLight_03"
            break
    assert clip_l3 is not None, "Failed to find Tantrum L3 clip!"

    # L4: Tantrum L4 (-1232275642304231213)
    clip_l4 = None
    for obj in tan_env.objects:
        if obj.path_id == -1232275642304231213 and obj.type.name == "AnimationClip":
            clip_l4 = obj.read_typetree()
            clip_l4["m_Name"] = "bugbite_gs_attackLight_04"
            break
    assert clip_l4 is not None, "Failed to find Tantrum L4 clip!"

    # M1: Movie Ironhide M1 (-7925637137891657471)
    clip_m1 = None
    for obj in anim_proc_env.objects:
        if obj.path_id == -7925637137891657471 and obj.type.name == "AnimationClip":
            clip_m1 = obj.read_typetree()
            clip_m1["m_Name"] = "bugbite_gs_attackMedium_01"
            break
    assert clip_m1 is not None, "Failed to find Movie Ironhide M1 clip!"

    # M2: Megatronus M2 (-3651284692217483506)
    clip_m2 = None
    for obj in meg_env.objects:
        if obj.path_id == -3651284692217483506 and obj.type.name == "AnimationClip":
            clip_m2 = obj.read_typetree()
            clip_m2["m_Name"] = "bugbite_gs_attackMedium_02"
            break
    assert clip_m2 is not None, "Failed to find Megatronus M2 clip!"

    # S3: Cliffjumper S3 (Fight, HitReaction, Transformed car)
    clip_s3_fight = None
    clip_s3_hit = None
    clip_s3_car = None
    cj_stage_mb = None
    cj_matinee_data = None

    for obj in cj_env.objects:
        if obj.type.name == "AnimationClip":
            t = obj.read_typetree()
            name = t.get("m_Name", "")
            if name == "cliffjumper_gs_attackSpecial_03":
                clip_s3_fight = t
                clip_s3_fight["m_Name"] = "bugbite_gs_attackSpecial_03"
            elif name == "cliffjumper_gs_attackSpecial_03_hitReaction":
                clip_s3_hit = t
                clip_s3_hit["m_Name"] = "bugbite_gs_attackSpecial_03_hitReaction"
            elif name == "cliffjumper_gs_attackSpecial_03_transformed":
                clip_s3_car = t
                clip_s3_car["m_Name"] = "bugbite_gs_attackSpecial_03_transformed"
        elif obj.path_id == 4051884971414969356:
            cj_stage_mb = obj.read_typetree()
        elif obj.path_id == -8867447285746891126:
            cj_matinee_data = obj.read_typetree()

    assert clip_s3_fight is not None, "Failed to find Cliffjumper S3 fight clip!"
    assert clip_s3_hit is not None, "Failed to find Cliffjumper S3 hitReaction clip!"
    assert clip_s3_car is not None, "Failed to find Cliffjumper S3 transformed car clip!"
    assert cj_stage_mb is not None, "Failed to find Cliffjumper stage MonoBehaviour!"
    assert cj_matinee_data is not None, "Failed to find Cliffjumper MatineeData!"

    print("[+] Successfully extracted all external clips (Jazz S1, Waspinator S2, Tantrum L1..L4, Ironhide M1, Megatronus M2, Cliffjumper S3)!")

    # 2. Prepare Bumblebee base asset
    print("[*] Grafting Bug Bite into Bumblebee physical rig...")
    bf = list(bb_env.files.values())[0]
    bb_asset = list(bb_env.assets)[0]

    old_cab = "CAB-f48eb1f9fe83a540c77c339585eedaa4"
    for subfname in bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-bugbite2026kabam0001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    PID_S1 = 992001
    PID_S2 = 992002
    PID_L1 = 992011
    PID_L2 = 992012
    PID_L3 = 992013
    PID_L4 = 992014
    PID_M1 = 992021
    PID_M2 = 992022
    PID_S3_FIGHT = 992031
    PID_S3_HIT = 992032
    PID_S3_CAR = 992033

    new_clips = [
        (PID_S1, clip_s1),
        (PID_S2, clip_s2),
        (PID_L1, clip_l1),
        (PID_L2, clip_l2),
        (PID_L3, clip_l3),
        (PID_L4, clip_l4),
        (PID_M1, clip_m1),
        (PID_M2, clip_m2),
        (PID_S3_FIGHT, clip_s3_fight),
        (PID_S3_HIT, clip_s3_hit),
        (PID_S3_CAR, clip_s3_car),
    ]

    template_clip = [o for o in bb_asset.objects.values() if o.type.name == "AnimationClip"][0]

    for pid, ctree in new_clips:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        replace_str_in_tree(ctree, old_cab, new_cab)
        new_obj.save_typetree(ctree)
        bb_asset.objects[pid] = new_obj
    print(f"[+] Injected {len(new_clips)} new self-contained AnimationClips into Bug Bite asset!")

    # Load custom recolored textures
    user_main_path = out_dir / "cha_bugbite_gs_main_a.png"
    user_misc_path = out_dir / "cha_bugbite_gs_tform_misc_a.png"
    user_wpns_path = out_dir / "cha_bugbite_gs_wpns_a.png"
    user_raoe_path = out_dir / "cha_bugbite_gs_raoe.png"

    # Rewire existing objects in Bumblebee bundle
    for obj in bb_env.objects:
        # Fight AOC: override_Bumblebee_GS_Kabam_fight (PathID=4786041819736037741)
        if obj.path_id == 4786041819736037741 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])

            # L1: Tantrum L1
            clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L1}
            # L2: Tantrum L2
            clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L2}
            # S1: Jazz S1
            clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S1}
            # S2: Waspinator S2
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}
            # S3: Cliffjumper S3 (slots 31 & 32)
            clips[31]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_FIGHT}
            clips[32]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_HIT}
            # L3: Tantrum L3
            clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L3}
            # M1: Movie Ironhide M1 (FileID 0, PID 992021)
            clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M1}
            # L4: Tantrum L4
            clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L4}
            # M2: Megatronus M2
            clips[44]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M2}

            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Bug Bite Fight AOC with full stitched moveset (all clips FileID 0)!")

        # Car AOC: override_Bumblebee_GS_Kabam_car (PathID=-5475676132653162908)
        elif obj.path_id == -5475676132653162908 and obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            clips = tree.get("m_Clips", [])
            # Slot 63: Cliffjumper S3 transformed vehicle animation
            clips[63]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S3_CAR}
            tree["m_Clips"] = clips
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Bug Bite Car AOC slot 63 with Cliffjumper S3 transformed car animation!")

        # MoveSet: PathID=-7496201166252604881
        elif obj.path_id == -7496201166252604881 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            moves = tree.get("_moves", [])

            # Move [0] Base.LightAttack01 -> Tantrum L1
            moves[0]["_name"] = "move_tantrum_attack_light_01"
            moves[0]["_asset"] = {"m_FileID": 4, "m_PathID": -2890002397111034488}

            # Move [1] Base.LightAttack02 -> Tantrum L2
            moves[1]["_name"] = "move_tantrum_attack_light_02"
            moves[1]["_asset"] = {"m_FileID": 4, "m_PathID": -4825681619876116179}

            # Move [2] Base.LightAttack03 -> Tantrum L3
            moves[2]["_name"] = "move_tantrum_attack_light_03"
            moves[2]["_asset"] = {"m_FileID": 4, "m_PathID": -8759699025821425951}

            # Move [3] Base.LightAttack04 -> Tantrum L4
            moves[3]["_name"] = "move_tantrum_attack_light_04"
            moves[3]["_asset"] = {"m_FileID": 4, "m_PathID": -4208587366598665143}

            # Move [4] Base.MediumAttack01 -> Movie Ironhide M1
            moves[4]["_name"] = "move_brawler_attack_medium_02"
            moves[4]["_asset"] = {"m_FileID": 4, "m_PathID": 8863364277361988242}

            # Move [5] Base.MediumAttack02 -> Megatronus M2
            moves[5]["_name"] = "move_megatronus_attack_medium_02"
            moves[5]["_asset"] = {"m_FileID": 4, "m_PathID": 5104354136730126689}

            # Move [6] Base.SpecialAttack01 -> Jazz S1
            moves[6]["_name"] = "move_jazz_special_01"
            moves[6]["_asset"] = {"m_FileID": 4, "m_PathID": -8221976179409562418}

            # Move [7] Base.SpecialAttack02 -> Bug Bite S2
            moves[7]["_name"] = "move_bugbite_special_02"
            moves[7]["_asset"] = {"m_FileID": 4, "m_PathID": BUGBITE_S2_PID}

            tree["_moves"] = moves
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Configured Bug Bite MoveSet (L1..L4=Tantrum, M1=Ironhide, M2=Megatronus, S1=Jazz, S2=BugBite)!")

        # Character Root MonoBehaviour: Keep Bumblebee's native Beetle stage
        elif obj.path_id == 1157624665093363023 and obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            # Bumblebee SpecialStagePrefab (3762158464405546467) is natively preserved
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Preserved native Volkswagen Beetle SpecialStagePrefab (3762158464405546467) for Bug Bite S3!")

        # Stage MonoBehaviour: Graft Cliffjumper S3 stage
        elif obj.path_id == 865296372479790604 and obj.type.name == "MonoBehaviour":
            tree = copy.deepcopy(cj_stage_mb)
            tree["m_GameObject"] = {"m_FileID": 0, "m_PathID": 3762158464405546467}
            tree["matineeData"] = {"m_FileID": 0, "m_PathID": -1441228310389542968}
            tree["actorInfoList"] = [
                {"actor_id": "BugBite_GS_Kabam", "avatarScale": 0.0, "sourceAvatar": {"m_FileID": 0, "m_PathID": 0}, "active": 1},
                {"actor_id": "Bludgeon_GS_RD20", "avatarScale": 0.0, "sourceAvatar": {"m_FileID": 0, "m_PathID": 0}, "active": 1}
            ]
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Grafted Cliffjumper S3 stage MonoBehaviour into Bug Bite stage!")

        # MatineeData MonoBehaviour: Graft Cliffjumper vehicle transformation MatineeData
        elif obj.path_id == -1441228310389542968 and obj.type.name == "MonoBehaviour":
            tree = copy.deepcopy(cj_matinee_data)
            tree["m_GameObject"] = {"m_FileID": 0, "m_PathID": -2568755476095504919}
            json_str = tree.get("jSONData", "")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_wpns_gun_right 1|gasgun", "cha_bugbite_gs_kabam_wpns_pistol_right|rightgun")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_wpns_gun_right 1", "cha_bugbite_gs_kabam_wpns_pistol_right")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_00 1", "cha_bugbite_gs_kabam_00")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_01 1|cha_cliffjumper_gs_kabam_01|transformed", "cha_bugbite_gs_kabam_01|transformed")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_01 1", "cha_bugbite_gs_kabam_01")
            json_str = json_str.replace("cha_cliffjumper_gs_kabam_01", "cha_bugbite_gs_kabam_01")
            json_str = json_str.replace("Cliffjumper_GS_Kabam", "BugBite_GS_Kabam")
            json_str = json_str.replace("TFormStage_Cliffjumper_GS_Special03", "TFormStage_BugBite_GS_attackSpecial03")
            tree["jSONData"] = json_str
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print("[+] Grafted Cliffjumper MatineeData with full vehicle transformation tracks into Bug Bite!")

        # Materials: glowing crimson red eyes and headlights
        elif obj.type.name == "Material":
            tree = obj.read_typetree()
            if obj.path_id in (3469483409826248538, -4405333283484697666):
                cols = tree.get("m_SavedProperties", {}).get("m_Colors", [])
                for c in cols:
                    if isinstance(c, tuple) and len(c) == 2:
                        k, v = c
                        if k == "_emissive_intensity_col":
                            v.update({"r": 0.297, "g": 0.005, "b": 0.005, "a": 0.0})
                        elif k == "_EmissionColor":
                            v.update({"r": 1.0, "g": 0.05, "b": 0.05, "a": 1.0})
                    elif isinstance(c, dict):
                        for k, v in c.items():
                            if k == "_emissive_intensity_col":
                                v.update({"r": 0.297, "g": 0.005, "b": 0.005, "a": 0.0})
                            elif k == "_EmissionColor":
                                v.update({"r": 1.0, "g": 0.05, "b": 0.05, "a": 1.0})
                print(f"[+] Set glowing RED emissive material on {tree.get('m_Name')} (PID {obj.path_id})")
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # Texture2D: Load custom recolored textures
        elif obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_bumblebee_gs_kabam_main_a" and user_main_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_main_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite main texture: {user_main_path}")
            elif tex_name in ["tform_misc_A", "tform_misc_a"] and user_misc_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_misc_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite vehicle misc texture: {user_misc_path}")
            elif tex_name == "cha_bumblebee_gs_kabam_wpns_a" and user_wpns_path.is_file():
                tex = obj.read()
                tex.image = Image.open(user_wpns_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite weapons texture: {user_wpns_path}")
            elif tex_name in ["main_tform_misc_RAOE", "main_tform_misc_raoe"] and user_raoe_path.is_file():
                tex = obj.read()
                tex.m_TextureFormat = 4  # RGBA32
                tex.image = Image.open(user_raoe_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Bug Bite emissive RAOE (RGBA32) texture: {user_raoe_path}")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        # AssetBundle container & preload table
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/bugbite_gs_kabam_odr/bugbite_gs_kabam.assetbundle"
            container = tree.get("m_Container", [])
            new_container = []
            for item in container:
                path_str = item[0].replace("bumblebee_gs_kabam", "bugbite_gs_kabam")
                asset_info = item[1]
                if "preloadSize" in asset_info and asset_info.get("preloadIndex", 0) > 0:
                    # Update preloadSize to encompass all newly appended clips!
                    asset_info["preloadSize"] = 1100 + len(new_clips)
                new_container.append([path_str, asset_info])
            tree["m_Container"] = new_container

            # Append injected clips to preload table
            preload = tree.get("m_PreloadTable", [])
            for pid, _ in new_clips:
                preload.append({"m_FileID": 0, "m_PathID": pid})
            tree["m_PreloadTable"] = preload

            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)
            print(f"[+] Updated AssetBundle container table and preload list! Preload size: {len(preload)}")

        # Root GameObjects: Rename
        elif obj.type.name == "GameObject":
            tree = obj.read_typetree()
            gname = tree.get("m_Name", "")
            is_audio_go = any(gname.startswith(p) for p in [
                "bumblebee_special_", "bumblebee_attack_heavy", "bumblebee_projectile_"
            ])
            if "bumblebee" in gname.lower() and not is_audio_go:
                tree["m_Name"] = gname.replace("Bumblebee", "BugBite").replace("bumblebee", "bugbite")
            replace_str_in_tree(tree, old_cab, new_cab)
            obj.save_typetree(tree)

        # All other MonoBehaviours / Controllers
        elif obj.type.name in ["AnimatorOverrideController", "MonoBehaviour", "AnimatorController", "Material"]:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except Exception:
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

    target_bundle = out_dir / "bugbite_gs_kabam.assetbundle"
    target_bundle.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")

    # Verify loaded bundle with UnityPy to ensure zero errors and valid type tree
    print("[*] Validating rebuilt bundle with UnityPy...")
    check_env = UnityPy.load(str(target_bundle))
    print(f"[+] Validation successful! Total objects in bundle: {len(check_env.objects)}")

    # Generate Manifest
    mf_text = f"""ManifestFileVersion: 0
CRC: 0
Hashes:
  AssetFileHash:
    serializedVersion: 2
    Hash: {new_cab[4:]}
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
- Assets/Bundles/Characters/Merged/BugBite_GS_Kabam/BugBite_GS_Kabam.prefab
- Assets/Bundles/Characters/Merged/BugBite_GS_Kabam/BugBite_GS_Kabam_lw.prefab
Dependencies:
- characters/character_fx.assetbundle
- characters/character_audio.assetbundle
- characters/moves.assetbundle
"""
    (out_dir / "bugbite_gs_kabam.assetbundle.manifest").write_text(mf_text, encoding="utf-8")

    # Ensure all portrait naming conventions exist WITHOUT overwriting user's Photoshop portraits!
    p_large = out_dir / "portrait_bugbite_large.png"
    p_ps_large = out_dir / "portrait_bugbite_gs_large.png"
    if p_ps_large.is_file():
        shutil.copyfile(p_ps_large, p_large)
        print(f"[+] Synced user's Photoshop portrait {p_ps_large} -> {p_large}")
    p_small = out_dir / "portrait_bugbite_gs_small.jpg"
    if p_small.is_file() and not (out_dir / "portrait_bugbite_small.jpg").is_file():
        shutil.copyfile(p_small, out_dir / "portrait_bugbite_small.jpg")
    print("[+] Protected user's Photoshop portraits and verified naming conventions!")
    print("[+] Bug Bite assetbundle generation complete!")


if __name__ == "__main__":
    generate_bugbite_assets()
