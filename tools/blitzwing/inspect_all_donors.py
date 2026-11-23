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

# Check moves.assetbundle for all required melee & special move names
env_moves = UnityPy.load(str(ROOT_BL / "assets_netflix" / "moves.assetbundle"))
move_map = {}
for o in env_moves.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        move_map[tt.get("m_Name", "")] = o.path_id

print("=== Searching melee moves in moves.assetbundle ===")
for kw in ["prowl", "cheetor", "rhinox", "wheeljack", "kickback", "motormaster"]:
    hits = sorted([k for k in move_map if kw in k.lower()])
    print(f"  [{kw}]: {[(h, move_map[h]) for h in hits]}")

# Inspect donor character bundles for MoveSet + AOC + Clip FileID/PathIDs
donors = {
    "motormaster": ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle",
    "mixmaster":   ROOT_GM / "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle",
    "bludgeon":    ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle",
    "windblade":   ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle",
    "sideswipe":   ROOT_BL / "extracted_apk/assets/assetpack/sideswipe_gs_odr/sideswipe_gs.assetbundle",
    "prowl":       ROOT_GM / "extracted_apk/assets/assetpack/prowl_gs_deluxe2016_odr/prowl_gs_deluxe2016.assetbundle",
    "cheetor":     ROOT_BL / "extracted_apk/assets/assetpack/cheetor_bw_transmetal_odr/cheetor_bw_transmetal.assetbundle",
    "rhinox":      ROOT_GM / "extracted_apk/assets/assetpack/rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle",
    "wheeljack":   ROOT_BL / "extracted_apk/assets/assetpack/wheeljack_gs_mp20_odr/wheeljack_gs_mp20.assetbundle",
    "kickback":    ROOT_GM / "extracted_apk/assets/assetpack/kickback_gs_kabam_odr/kickback_gs_kabam.assetbundle",
}

# Build map of Megatron AC clip PathID -> AOC slot index for FIGHT_AOC
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
meg_aoc_orig_to_slot = {}
for o in meg_env.objects:
    if o.path_id == -7755666207738536548:
        aoc = o.read_typetree()
        for idx, c in enumerate(aoc["m_Clips"]):
            pid = c["m_OriginalClip"]["m_PathID"]
            if pid != 0:
                meg_aoc_orig_to_slot[pid] = idx

for dname, dpath in donors.items():
    print(f"\n==================== DONOR: {dname} ====================")
    env = UnityPy.load(str(dpath))
    omap = {o.path_id: o for o in env.objects}
    ext_map = {}
    for _, f in env.file.files.items():
        if hasattr(f, "externals"):
            for i, e in enumerate(f.externals, start=1):
                ext_map[i] = e.path
    # Find fight MoveSet
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_moves" in tt and len(tt["_moves"]) > 20:
                print(f"  MoveSet (len={len(tt['_moves'])}):")
                for m in tt["_moves"]:
                    st = m.get("_animStateName", "")
                    if any(x in st for x in ("LightAttack", "MediumAttack", "SpecialAttack01", "SpecialAttack02", "RangedAttack")):
                        ast = m.get("_asset", {})
                        print(f"    {st:<22} -> {m.get('_name'):<42} asset=({ast.get('m_FileID')}, {ast.get('m_PathID')})")
    # Find fight AOC (match against meg_aoc_orig_to_slot)
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            clips = tt.get("m_Clips", [])
            if len(clips) > 40:
                print(f"  AOC '{tt.get('m_Name')}' (len={len(clips)}):")
                for c in clips:
                    orig_pid = c["m_OriginalClip"]["m_PathID"]
                    slot = meg_aoc_orig_to_slot.get(orig_pid)
                    if slot in (2, 3, 4, 5, 18, 21, 22, 41, 42, 43, 44, 51, 52, 53):
                        ovr = c["m_OverrideClip"]
                        fid, opid = ovr["m_FileID"], ovr["m_PathID"]
                        cname = ""
                        if fid == 0 and opid in omap:
                            cname = omap[opid].read_typetree().get("m_Name", "")
                        elif fid in ext_map:
                            cname = f"ext:{ext_map[fid].split('/')[-1]}"
                        print(f"    meg_slot[{slot:02d}] orig={orig_pid} -> ovr=({fid}, {opid}) [{cname}]")
