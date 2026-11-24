import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# Check character_anim_procedural clips
proc_anim = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_anim_procedural.assetbundle"))
proc_clips = {}
for o in proc_anim.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        proc_clips[o.path_id] = tt.get("m_Name", "")

print(f"character_anim_procedural clips: {len(proc_clips)}")

check_clip_pids = {
    "Prowl L1": -5567779559826134777,
    "Cheetor L2": -486271743690878734,
    "Rhinox L3": 93276785253583668,
    "Rhinox M2": -6442010242213229130,
    "Wheeljack M1": 7265497203347661852,
    "Kickback M2": 221766495520085048,
    "Mixmaster S1": -7921770726548403079,
    "Bludgeon S2": -5815229600094096883,
    "Windblade S1": 4130864494046913653,
    "Sideswipe S2": -8047270946990567681,
    "Motormaster R1": -3948795660449728024,
    "Motormaster R2": 6078334979657561662,
    "Motormaster R3": 8599663582438923052,
}
for label, pid in check_clip_pids.items():
    print(f"  {label:<16} ({pid}): in_proc={pid in proc_clips} name='{proc_clips.get(pid, '')}'")

# Check unused clip slots in megatron_gs_leader2015
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
meg_clips = {}
for o in meg_env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        meg_clips[o.path_id] = tt.get("m_Name", "")
print(f"\nMegatron local AnimationClips ({len(meg_clips)}):")
for pid, name in sorted(meg_clips.items(), key=lambda x: x[1]):
    print(f"  {pid:<22} '{name}'")

# Check unused slots in override_Megatron_GS_Leader2015_fight (e.g. slots 63-66 or replaced melee/ranged/sp clips)
for o in meg_env.objects:
    if o.path_id == -7755666207738536548:
        aoc = o.read_typetree()
        print("\nMegatron Fight AOC local clip overrides:")
        for idx, c in enumerate(aoc["m_Clips"]):
            ovr = c["m_OverrideClip"]
            if ovr["m_FileID"] == 0 and ovr["m_PathID"] != 0:
                print(f"  slot[{idx:02d}] local_pid={ovr['m_PathID']} name='{meg_clips.get(ovr['m_PathID'], '?')}'")

# Check Megatron root PrefabList & external CABs
print("\n=== Checking Mixmaster & Sideswipe Projectiles/FX ===")
for label, bpath, kw in [
    ("Mixmaster", ROOT_GM / "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle", "projectile_special_bullet"),
    ("Sideswipe", ROOT_BL / "extracted_apk/assets/assetpack/sideswipe_gs_odr/sideswipe_gs.assetbundle", "projectile_sideswipe_missile"),
    ("Motormaster", ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle", "projectile_optimus_bullet"),
]:
    env = UnityPy.load(str(bpath))
    omap = {o.path_id: o for o in env.objects}
    print(f"\n[{label}] searching '{kw}' & PrefabList:")
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "PrefabList" in tt or "m_Prefabs" in tt:
                plist = tt.get("PrefabList", tt.get("m_Prefabs", []))
                for it in plist:
                    p = it.get("Prefab", {})
                    fid, pid = p.get("m_FileID", 0), p.get("m_PathID", 0)
                    name = omap[pid].read_typetree().get("m_Name", "") if (fid == 0 and pid in omap) else ""
                    if any(x in name.lower() or kw.split("_")[-1] in name.lower() for x in ("bullet", "missile", "fx_p_mix", "fx_p_optimus", "fx_p_red")) or (fid != 0):
                        print(f"  PrefabList({o.path_id}): ({fid}, {pid}) '{name}' amt={it.get('Amount')}")
        elif o.type.name == "GameObject":
            tt = o.read_typetree()
            if kw in tt.get("m_Name", "") or "fx_p_mixmaster" in tt.get("m_Name", "") or "fx_p_windblade" in tt.get("m_Name", ""):
                print(f"  GO '{tt['m_Name']}' PID={o.path_id}")

# Check Windblade & Bludgeon for fx_p_windblade_radius, sword Prop / AOC
for label, bpath in [
    ("Windblade", ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle"),
    ("Bludgeon", ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle"),
]:
    env = UnityPy.load(str(bpath))
    print(f"\n[{label}] FX & Sword Props:")
    for o in env.objects:
        if o.type.name == "GameObject":
            tt = o.read_typetree()
            nm = tt.get("m_Name", "").lower()
            if "fx_p_windblade" in nm or "fx_p_acid" in nm or "sword" in nm:
                print(f"  GO '{tt['m_Name']}' PID={o.path_id}")
        elif o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_props" in tt:
                for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                    if "sword" in k.lower():
                        print(f"  PropsController({o.path_id}) key='{k}' InitFlags={v.get('InitFlags')} RootPath='{v.get('RootPath')}' Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} AOC={v.get('OverrideController')}")
