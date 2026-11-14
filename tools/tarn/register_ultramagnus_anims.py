import sys
from copy import copy
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Agent\TFTF-blender")
BP_UM = ROOT / "extracted_apk" / "assets" / "assetpack" / "ultramagnus_gs_leader_odr" / "ultramagnus_gs_leader.assetbundle"
BP_PROC = ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"
OUT_BP = ROOT / "toolchain" / "ultramagnus_anims_registered.assetbundle"
OUT_BP.parent.mkdir(parents=True, exist_ok=True)


def main():
    print("Loading character_anim_procedural.assetbundle...")
    env_proc = UnityPy.load(str(BP_PROC))
    target_clips = {
        "tactical_normal_idle",
        "Prefight_Tactical_idle",
        "TeamSelect_Brawler_idle",
        "brawler_normal_locoRun",
        "Brute_Normal_Block",
        "Brute_Normal_locoDash_Loop",
        "tactical_normal_attacklight_01_jab_L",
        "tactical_normal_attacklight_02_jab_R",
        "tactical_normal_attacklight_03_hook_L",
        "tactical_normal_attacklight_04_uppercut_R",
        "tactical_normal_attackMedium_01_elbow_L_01",
        "tactical_normal_attackMedium_02_kick_R",
        "dual pistols_attackRanged_gun_01",
        "dual pistols_attackRanged_gun_02",
        "dual pistols_attackRanged_gun_03",
        "Ultramagnus_Normal_victory",
        "Ultramagnus_Normal_victory_idle",
        "frontend_Ultramagnus_gs_levelup_vehicle_idle_transformed",
        "frontend_Ultramagnus_gs_levelup_enter_transformed",
        "frontend_Ultramagnus_gs_levelup_exit_transformed",
        "BattleIntro_Trucks_ultramagnus_transformed",
    }

    extracted = {}
    for obj in env_proc.objects:
        if obj.type.name == "AnimationClip":
            name = obj.read_typetree().get("m_Name", "")
            if name in target_clips:
                extracted[name] = obj.read_typetree()
                print(f"  [+] Extracted from procedural: '{name}'")

    missing = sorted(target_clips - set(extracted.keys()))
    if missing:
        print(f"  [!] Missing from procedural: {missing}")

    print("Loading ultramagnus_gs_leader.assetbundle...")
    env_um = UnityPy.load(str(BP_UM))
    anim_entries = {}
    for obj in env_um.objects:
        if obj.type.name == "AnimationClip":
            name = obj.read_typetree().get("m_Name", "")
            anim_entries[name] = obj.path_id
            anim_entries[f"assets/anims/{name.lower()}.anim"] = obj.path_id
            anim_entries[f"assets/anims/{name}.anim"] = obj.path_id
            print(f"  [+] Existing UM clip: '{name}'")

    sf = next(f for f in env_um.file.files.values() if hasattr(f, "objects"))
    max_pid = max(obj.path_id for obj in env_um.objects)
    proto_clip = next(o for o in env_um.objects if o.type.name == "AnimationClip")

    for name, tree in extracted.items():
        if name in anim_entries:
            continue
        max_pid += 1
        tree["m_Name"] = name
        new_reader = copy(proto_clip)
        new_reader.path_id = max_pid
        new_reader.save_typetree(tree)
        sf.objects[max_pid] = new_reader
        anim_entries[name] = max_pid
        anim_entries[f"assets/anims/{name.lower()}.anim"] = max_pid
        anim_entries[f"assets/anims/{name}.anim"] = max_pid

    for obj in env_um.objects:
        if obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            c = tree.get("m_Container", [])
            existing = {item[0] for item in c}
            for name, pid in anim_entries.items():
                if name not in existing:
                    c.append((name, {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": pid}}))
            tree["m_Container"] = c
            obj.save_typetree(tree)
            break

    with open(OUT_BP, "wb") as f:
        f.write(env_um.file.save(packer="lz4"))
    print(f"[✓] Saved registered UM clips bundle -> {OUT_BP} ({OUT_BP.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
