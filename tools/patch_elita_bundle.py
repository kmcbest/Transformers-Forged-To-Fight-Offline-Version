import sys
import copy
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def patch_elita_bundle():
    target_bundle_path = Path(r"E:\Agent\TFTF\assets_redeco\elita_one_gs.assetbundle")
    assert target_bundle_path.exists(), f"Target bundle not found: {target_bundle_path}"

    print(f"[*] Loading target bundle: {target_bundle_path}")
    env_elita = UnityPy.load(str(target_bundle_path))
    elita_asset = list(env_elita.assets)[0]

    # Template clip to clone
    template_clip = [o for o in elita_asset.objects.values() if o.type.name == "AnimationClip"][0]

    # 1. Load Optimus clips from characters.assetbundle
    char_bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\characters\characters.assetbundle")
    print(f"[*] Loading characters bundle: {char_bundle_path}")
    env_char = UnityPy.load(str(char_bundle_path))

    optimus_clip_ids = {
        "brawler2_normal_attackLight_01_hook": -3430411122056989002,
        "brawler2_normal_attackLight_02_hook": -4356099580166283104,
        "brawler2_normal_attackLight_03_reversePunch": -7735719043025414755,
        "brawler2_normal_attackLight_04_frontkick_R": 435286042547748284,
        "brawler2_normal_attackMedium_01_uppercut": 2377444956165013633,
        "brawler2_normal_attackMedium_02_sidekick": 3356339846923504230,
    }

    optimus_clips = {}
    for o in env_char.objects:
        if o.path_id in optimus_clip_ids.values():
            tree = o.read_typetree()
            optimus_clips[o.path_id] = tree
            print(f"  [+] Found Optimus clip: {tree.get('m_Name')} (orig path_id {o.path_id})")

    assert len(optimus_clips) == 6, f"Failed to find all 6 Optimus melee clips! Found {len(optimus_clips)}"

    # 2. Load Bumblebee S2 clip from bumblebee_cin_dotm.assetbundle
    bb_bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\bumblebee_cin_dotm_odr\bumblebee_cin_dotm.assetbundle")
    print(f"[*] Loading Bumblebee bundle: {bb_bundle_path}")
    env_bb = UnityPy.load(str(bb_bundle_path))

    bb_s2_tree = None
    for o in env_bb.objects:
        if o.path_id == -2410350876026679100:
            bb_s2_tree = o.read_typetree()
            print(f"  [+] Found Bumblebee S2 clip: {bb_s2_tree.get('m_Name')}")
            break

    assert bb_s2_tree is not None, "Failed to find Bumblebee S2 clip bumble_bee_attackSpecial_02!"

    # 3. Dedicated PathIDs for injected clips
    PID_L1 = 992001
    PID_L2 = 992002
    PID_L3 = 992003
    PID_L4 = 992004
    PID_M1 = 992005
    PID_M2 = 992006
    PID_S2 = 992007

    clips_to_inject = [
        (PID_L1, optimus_clips[optimus_clip_ids["brawler2_normal_attackLight_01_hook"]]),
        (PID_L2, optimus_clips[optimus_clip_ids["brawler2_normal_attackLight_02_hook"]]),
        (PID_L3, optimus_clips[optimus_clip_ids["brawler2_normal_attackLight_03_reversePunch"]]),
        (PID_L4, optimus_clips[optimus_clip_ids["brawler2_normal_attackLight_04_frontkick_R"]]),
        (PID_M1, optimus_clips[optimus_clip_ids["brawler2_normal_attackMedium_01_uppercut"]]),
        (PID_M2, optimus_clips[optimus_clip_ids["brawler2_normal_attackMedium_02_sidekick"]]),
        (PID_S2, bb_s2_tree)
    ]

    for pid, ctree in clips_to_inject:
        new_obj = copy.copy(template_clip)
        new_obj.path_id = pid
        new_obj.save_typetree(ctree)
        elita_asset.objects[pid] = new_obj
        print(f"  [+] Injected AnimationClip '{ctree.get('m_Name')}' with PathID {pid}")

    # 4. Update override_Arcee_GS_Deluxe2014_fight AOC (PathID -1743739782552134489)
    fight_aoc_found = False
    for o in elita_asset.objects.values():
        if o.path_id == -1743739782552134489 and o.type.name == "AnimatorOverrideController":
            tree = o.read_typetree()
            clips = tree.get("m_Clips", [])

            # Check original clips before updating
            # Slot [2]: char_attackLight_01 -> PID_L1
            assert clips[2]["m_OriginalClip"]["m_PathID"] == 3149807030316843707
            clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L1}

            # Slot [3]: char_attackLight_02 -> PID_L2
            assert clips[3]["m_OriginalClip"]["m_PathID"] == 1493990355315399625
            clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L2}

            # Slot [5]: char_attackSpecial_02 -> PID_S2
            assert clips[5]["m_OriginalClip"]["m_PathID"] == 4730099292729452391
            clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_S2}

            # Slot [41]: char_attackLight_03 -> PID_L3
            assert clips[41]["m_OriginalClip"]["m_PathID"] == -8618744054794967589
            clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L3}

            # Slot [42]: char_attackMedium_01 -> PID_M1
            assert clips[42]["m_OriginalClip"]["m_PathID"] == 424597727730099647
            clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M1}

            # Slot [43]: char_attackLight_04 -> PID_L4
            assert clips[43]["m_OriginalClip"]["m_PathID"] == 7758611357151580349
            clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_L4}

            # Slot [44]: char_attackMedium_02 -> PID_M2
            assert clips[44]["m_OriginalClip"]["m_PathID"] == 1189595235236326705
            clips[44]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_M2}

            tree["m_Clips"] = clips
            o.save_typetree(tree)
            fight_aoc_found = True
            print("  [+] Successfully updated override_Arcee_GS_Deluxe2014_fight AOC with 6 Optimus melee clips + Bumblebee S2!")
            break

    assert fight_aoc_found, "Fight AOC not found in elita bundle!"

    # 5. Update MoveSet MonoBehaviour (PathID -4848773121996721726)
    moveset_found = False
    for o in elita_asset.objects.values():
        if o.path_id == -4848773121996721726 and o.type.name == "MonoBehaviour":
            tree = o.read_typetree()
            moves = tree.get("_moves", [])
            for m in moves:
                st = m.get("_animStateName")
                if st == "Base.LightAttack01":
                    m["_name"] = "move_brawler_2_attack_light_01"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": 6034126977261442960}
                elif st == "Base.LightAttack02":
                    m["_name"] = "move_brawler_2_attack_light_02"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": 1957860170544410956}
                elif st == "Base.LightAttack03":
                    m["_name"] = "move_brawler_2_attack_light_03"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": -5920903051048406125}
                elif st == "Base.LightAttack04":
                    m["_name"] = "move_brawler_2_attack_light_04"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": -401702831497719379}
                elif st == "Base.MediumAttack01":
                    m["_name"] = "move_brawler_2_attack_medium_02"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": -8640470093563950672}
                elif st == "Base.MediumAttack02":
                    m["_name"] = "move_brawler_2_attack_medium_01"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": 479990204744469841}
                elif st == "Base.SpecialAttack02":
                    m["_name"] = "move_bumblebee_special_02"
                    m["_asset"] = {"m_FileID": 7, "m_PathID": -4614944415960066340}

            tree["_moves"] = moves
            o.save_typetree(tree)
            moveset_found = True
            print("  [+] Successfully updated MoveSet MonoBehaviour with Optimus G1 melee moves & Bumblebee S2!")
            break

    assert moveset_found, "MoveSet MonoBehaviour not found!"

    # 6. Update PrefabList MonoBehaviour (PathID -7737873523461476806)
    prefab_list_found = False
    for o in elita_asset.objects.values():
        if o.path_id == -7737873523461476806 and o.type.name == "MonoBehaviour":
            tree = o.read_typetree()
            plist = tree.get("PrefabList", [])
            existing_pids = {item["Prefab"]["m_PathID"] for item in plist if "Prefab" in item}

            # Add missing particle effects if not present
            s2_particles = [
                ({'m_FileID': 1, 'm_PathID': -8154008366814937611}, 2), # fx_p_bumblebee_muzzle
                ({'m_FileID': 1, 'm_PathID': -811174631493111739}, 5),  # fx_p_foot_drag_sparks
                ({'m_FileID': 1, 'm_PathID': -7324536193646862619}, 2), # fx_p_floor_fire_burnout
                ({'m_FileID': 2, 'm_PathID': -4752345455319617770}, 3), # fx_r_trail_bumblebee
                ({'m_FileID': 2, 'm_PathID': -1685458833540413680}, 2), # fx_p_hit_punch_sparks_special
            ]
            added_cnt = 0
            for pref, amt in s2_particles:
                if pref["m_PathID"] not in existing_pids:
                    plist.append({"Prefab": pref, "Amount": amt})
                    added_cnt += 1

            tree["PrefabList"] = plist
            o.save_typetree(tree)
            prefab_list_found = True
            print(f"  [+] Updated PrefabList: injected {added_cnt} missing Bumblebee S2 particles (total {len(plist)})")
            break

    assert prefab_list_found, "PrefabList MonoBehaviour not found!"

    # 7. Save AssetBundle with packer="lz4"
    print("[*] Re-packing AssetBundle with packer='lz4'...")
    saved_bytes = env_elita.file.save(packer="lz4")
    target_bundle_path.write_bytes(saved_bytes)
    print(f"[SUCCESS] Saved {target_bundle_path.name}: {len(saved_bytes):,} bytes ({len(saved_bytes)/1024/1024:.2f} MB)")

if __name__ == "__main__":
    patch_elita_bundle()
