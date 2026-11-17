import argparse
import copy
import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

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

def commit_obj_typetree(obj, tree_data):
    if hasattr(obj, "save_typetree"):
        obj.save_typetree(tree_data)
    else:
        obj.write_typetree(tree_data)

def generate_blackout_assets(output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    grindor_bundle_path = Path("extracted_apk/assets/assetpack/grindor_cin_rotf_odr/grindor_cin_rotf.assetbundle")
    necro_bundle_path = Path("extracted_apk/assets/assetpack/necrotronus_gs_kabam_odr/necrotronus_gs_kabam.assetbundle")

    print("[*] Loading source bundles...")
    g_env = UnityPy.load(str(grindor_bundle_path))
    n_env = UnityPy.load(str(necro_bundle_path))

    g_bf = list(g_env.files.values())[0]
    g_sf = list(g_env.assets)[0]
    n_sf = list(n_env.assets)[0]

    # 1. CAB Detection & Mapping
    old_cab = "CAB-8afd6aa044e27bb02d6a7286d95293b4"
    for subfname in g_bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-blackout2026cin0001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # 2. Extract & Inject Necrotronus Melee AnimationClips
    # Base controller mappings:
    # Slot 2 (char_attackLight_01) = L1: Hound_Cin_attackLight_01_leftPunch
    # Slot 3 (char_attackLight_02) = L2: brute_tantrum_attackLight_02_jab
    # Slot 41 (char_attackLight_03) = L3: tactical3_normal_attacklight_01_bodyjab_L
    # Slot 43 (char_attackLight_04) = L4: brute_tantrum_attackLight_04_uppcut
    # Slot 42 (char_attackMedium_01) = M1: tactical3_normal_attackMedium_01_shoulder_L
    # Slot 44 (char_attackMedium_02) = M2: tactical3_normal_attackMedium_02_frontkick_R
    necro_clip_map = {
        -1317812492983641037: (991101, "blackout_Cin_attackLight_01_leftPunch"),
         4342173990092517894: (991102, "blackout_attackLight_02_jab"),
        -4110902301780405690: (991103, "blackout_attacklight_01_bodyjab_L"),
        -1232275642304231213: (991104, "blackout_attackLight_04_uppcut"),
         7265497203347661852: (991105, "blackout_attackMedium_01_shoulder_L"),
        -1740342661625100663: (991106, "blackout_attackMedium_02_frontkick_R"),
    }

    template_clip = [o for o in g_sf.objects.values() if o.type.name == "AnimationClip"][0]
    injected_pids = []

    for src_pid, (dst_pid, new_name) in necro_clip_map.items():
        ctree = n_sf.objects[src_pid].read_typetree()
        ctree["m_Name"] = new_name
        replace_str_in_tree(ctree, old_cab, new_cab)

        new_obj = copy.copy(template_clip)
        new_obj.path_id = dst_pid
        commit_obj_typetree(new_obj, ctree)
        g_sf.objects[dst_pid] = new_obj
        injected_pids.append(dst_pid)
    print(f"[*] Injected {len(injected_pids)} Necrotronus melee clips into Blackout bundle.")

    # Paths to generated custom textures
    tex_main_path = Path("build/cha_blackout_cin_tf_main_a.png")
    tex_misc_path = Path("build/tform_misc_A.png")
    tex_wpns_path = Path("build/cha_blackout_cin_tf_wpns_a.png")

    # 3. Configure Fight AOC (PID 259380691726149969)
    aoc_obj = g_sf.objects[259380691726149969]
    aoc_tree = aoc_obj.read_typetree()
    clips = aoc_tree.get("m_Clips", [])

    # Exact slot wiring:
    # Slot 2 (char_attackLight_01) -> L1
    clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991101}
    # Slot 3 (char_attackLight_02) -> L2
    clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991102}
    # Slot 41 (char_attackLight_03) -> L3
    clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991103}
    # Slot 43 (char_attackLight_04) -> L4
    clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991104}
    # Slot 42 (char_attackMedium_01) -> M1
    clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991105}
    # Slot 44 (char_attackMedium_02) -> M2
    clips[44]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991106}

    # Slot 58 (char_attackHeavy) -> Grindor native heavy missile fire
    clips[58]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -7224602046215420873}

    # Specials:
    # Slot 4: S1 -> Shockwave S1
    clips[4]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 8733033661733578865}
    # Slot 5: S2 -> Movie Ironhide S2
    clips[5]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": 4043783240345789736}
    # Slots 31 & 32: S3 -> Grindor native preserved!

    # Victory:
    clips[39]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -7535929919115318753}
    clips[40]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4195553960651922483}

    aoc_tree["m_Clips"] = clips
    replace_str_in_tree(aoc_tree, old_cab, new_cab)
    commit_obj_typetree(aoc_obj, aoc_tree)
    print("[+] Configured Fight AOC (L1=Slot2, L2=Slot3, L3=Slot41, L4=Slot43, M1=Slot42, M2=Slot44, Heavy=Slot58)!")

    # 4. Configure MoveSet (PID -2282744758651308026)
    ms_obj = g_sf.objects[-2282744758651308026]
    ms_tree = ms_obj.read_typetree()
    moves = ms_tree["_moves"]

    moves[0]["_name"] = "move_megatronus_attack_light_01"
    moves[0]["_asset"] = {"m_FileID": 5, "m_PathID": -6740464737614209425}

    moves[1]["_name"] = "move_megatronus_attack_light_02"
    moves[1]["_asset"] = {"m_FileID": 5, "m_PathID": 2095223796171100125}

    moves[2]["_name"] = "move_megatronus_attack_light_03"
    moves[2]["_asset"] = {"m_FileID": 5, "m_PathID": 6374914769425836133}

    moves[3]["_name"] = "move_megatronus_attack_light_04"
    moves[3]["_asset"] = {"m_FileID": 5, "m_PathID": 8656719042657693179}

    moves[4]["_name"] = "move_megatronus_attack_medium_01"
    moves[4]["_asset"] = {"m_FileID": 5, "m_PathID": 3267735181318500007}

    moves[5]["_name"] = "move_megatronus_attack_medium_02"
    moves[5]["_asset"] = {"m_FileID": 5, "m_PathID": 5104354136730126689}

    # Dedicated Blackout specials in moves.assetbundle
    moves[6]["_name"] = "move_blackout_special_01"
    moves[6]["_asset"] = {"m_FileID": 5, "m_PathID": -8888888888888888891}

    moves[7]["_name"] = "move_blackout_special_02"
    moves[7]["_asset"] = {"m_FileID": 5, "m_PathID": -8888888888888888892}

    moves[44]["_name"] = "move_heavy_plane_shoot"
    moves[44]["_asset"] = {"m_FileID": 5, "m_PathID": -7784374527050455307}

    ms_tree["_moves"] = moves
    replace_str_in_tree(ms_tree, old_cab, new_cab)
    commit_obj_typetree(ms_obj, ms_tree)
    print("[+] Configured MoveSet (_moves[0..5]=Necrotronus Melee, _moves[6]=Blackout S1, _moves[7]=Blackout S2, _moves[44]=Heavy Plane Shoot)!")

    # 5. Configure PlayerReferences Victory Stage (PID 4809715625580256617)
    pref_obj = g_sf.objects[4809715625580256617]
    pref_tree = pref_obj.read_typetree()
    pref_tree["VictoryStagePrefab"] = {"m_FileID": 7, "m_PathID": 7184980468553159185}
    replace_str_in_tree(pref_tree, old_cab, new_cab)
    commit_obj_typetree(pref_obj, pref_tree)

    # 6. Inject Textures
    for obj in g_sf.objects.values():
        if obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name == "cha_grindor_cin_rotf_main_a" and tex_main_path.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_main_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Blackout main texture: {tex_main_path}")
            elif tex_name == "tform_misc_A" and tex_misc_path.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_misc_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Blackout vehicle misc texture: {tex_misc_path}")
            elif tex_name == "cha_grindor_cin_rotf_wpns_a" and tex_wpns_path.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_wpns_path).convert("RGBA")
                tex.save()
                print(f"[+] Injected custom Blackout weapons texture: {tex_wpns_path}")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)

    # 7. AssetBundle object: update container and preload table
    for obj in g_sf.objects.values():
        if obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/blackout_cin_tf_odr/blackout_cin_tf.assetbundle"
            container = tree.get("m_Container", [])
            new_container = []
            for item in container:
                path_str = item[0].replace("grindor_cin_rotf", "blackout_cin_tf").replace("rotf", "tf")
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container

            # Append only the 6 injected animation clips to preload table
            preload = tree.get("m_PreloadTable", [])
            existing_preload = set(p.get("m_PathID") for p in preload)
            for ipid in injected_pids:
                if ipid not in existing_preload:
                    preload.append({"m_FileID": 0, "m_PathID": ipid})
                    existing_preload.add(ipid)
            tree["m_PreloadTable"] = preload

            replace_str_in_tree(tree, old_cab, new_cab)
            commit_obj_typetree(obj, tree)
            print(f"[+] Updated AssetBundle container and preload list ({len(preload)} items)!")

    # 8. Deep CAB isolation across all objects (skipping already processed/committed objects)
    skip_pids = {
        259380691726149969,   # Fight AOC
        -2282744758651308026, # MoveSet
        -5353390358171322875, # PrefabLib
        4809715625580256617,  # PlayerReferences
    } | set(injected_pids)

    for pid, obj in g_sf.objects.items():
        if pid in skip_pids:
            continue
        if obj.type.name not in ["Texture2D", "AssetBundle"]:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)
            except Exception:
                pass

    # 9. Chapter 9 Quality Gate: Sort script_types ascending
    skeys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in g_sf.script_types]
    if skeys != sorted(skeys):
        print("[*] Sorting g_sf.script_types ascending...")
        old_to_new_sidx = {}
        sorted_script_types = sorted(
            enumerate(g_sf.script_types),
            key=lambda x: (x[1].local_serialized_file_index, x[1].local_identifier_in_file)
        )
        new_list = []
        for new_idx, (old_idx, sref) in enumerate(sorted_script_types):
            old_to_new_sidx[old_idx] = new_idx
            new_list.append(sref)
        g_sf.script_types = new_list
        for tp in g_sf.types:
            if tp.script_type_index >= 0:
                tp.script_type_index = old_to_new_sidx.get(tp.script_type_index, tp.script_type_index)

    # 10. Save rebuilt AssetBundle
    new_files = {}
    for subfname, subf in g_bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf

    g_bf.files = new_files
    g_bf.version = 7
    g_bf.version_engine = "2020.3.31f1"
    g_bf.version_player = "5.x.x"

    target_bundle = out_dir / "blackout_cin_tf.assetbundle"
    target_bundle.write_bytes(g_bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")
    print("[+] Blackout assetbundle generation complete!")

def main():
    parser = argparse.ArgumentParser(description="Generate Blackout (眩晕) composite assets.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_blackout_assets(output_dir=args.output)

if __name__ == "__main__":
    main()
