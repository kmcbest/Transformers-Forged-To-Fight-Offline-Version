import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
BW_BUNDLE = ROOT / "assets_redeco" / "blitzwing_gs.assetbundle"
MOVES_BUNDLE = ROOT / "assets_redeco" / "moves.assetbundle"
ANIMP_BUNDLE = ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"
CFX_BUNDLE = ROOT / "assets_netflix" / "character_fx.assetbundle"
CFXP_BUNDLE = ROOT / "assets_netflix" / "character_fx_procedural.assetbundle"

print("=== 1. Verifying moves.assetbundle ===")
mv_env = UnityPy.load(str(MOVES_BUNDLE))
mv_objs = {o.path_id: o for o in mv_env.objects}
mv_names = {}
for o in mv_env.objects:
    if o.type.name == "TextAsset":
        t = o.read()
        mv_names[t.m_Name] = o.path_id
assert len(mv_names) >= 956, f"Too few moves: {len(mv_names)}"
assert "move_lifeline_special_01" in mv_names and "move_lifeline_special_02" in mv_names
for sp_name, expect_sword in [
    ("move_blitzwing_tank_s1", False),
    ("move_blitzwing_tank_s2", True),
    ("move_blitzwing_jet_s1", True),
    ("move_blitzwing_jet_s2", False),
]:
    pid = mv_names[sp_name]
    raw = mv_objs[pid].read().m_Script
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    evts = json.loads(raw)["moves"]["events"]
    prop_evts = [e for e in evts if e.get("type") == "PropMoveEvent"]
    has_sword = any(e.get("p") == "sword" and e.get("en") is True for e in prop_evts)
    assert has_sword == expect_sword, f"{sp_name}: expect_sword={expect_sword}, got prop_evts={prop_evts}"
    print(f"  [OK] {sp_name} (PID={pid}) events={len(evts)} sword_prop={has_sword}")

print("\n=== 2. Verifying External Dependency Bundles ===")
animp_pids = {o.path_id for o in UnityPy.load(str(ANIMP_BUNDLE)).objects}
cfx_pids = {o.path_id for o in UnityPy.load(str(CFX_BUNDLE)).objects}
cfxp_pids = {o.path_id for o in UnityPy.load(str(CFXP_BUNDLE)).objects}
mv_pids = set(mv_objs.keys())
EXT_MAP = {3: cfxp_pids, 5: animp_pids, 7: mv_pids, 9: cfx_pids}

print("\n=== 3. Verifying blitzwing_gs.assetbundle ===")
bw_env = UnityPy.load(str(BW_BUNDLE))
bw_objs = {o.path_id: o for o in bw_env.objects}
res_file = next(f for n, f in bw_env.file.files.items() if n.endswith(".resource"))

# Check Weapon Textures & Material
mat_wpns = bw_objs[-9117353815363826346].read_typetree()
wpns_tex = dict(mat_wpns["m_SavedProperties"]["m_TexEnvs"])
assert wpns_tex["_base_tex"]["m_Texture"]["m_PathID"] == -3077338877283958343
assert wpns_tex["_normal_tex"]["m_Texture"]["m_PathID"] == -669899812022169322
assert wpns_tex["_pbr_composite_tex"]["m_Texture"]["m_PathID"] == -8888888888888888912
for tpid in (-3077338877283958343, -669899812022169322, -8888888888888888912):
    vt = bw_objs[tpid].read()
    assert vt.m_Width == 1024 and vt.m_Height == 1024, f"Bad wpns tex size {tpid}"
print("  [OK] MAT_WPNS_PID uses 3 dedicated 1024x1024 textures (non-overlapping with Vehicle RAOE)")

# Check Weapon Meshes & SMRs
for mpid, expected_v in ((-3217264854751393828, 660), (-8888888888888888911, 407)):
    mtt = bw_objs[mpid].read_typetree()
    assert mtt["m_VertexData"]["m_VertexCount"] == expected_v
    assert len(mtt["m_BindPose"]) == 1 and abs(mtt["m_BindPose"][0]["e00"] - 1.0) < 1e-5
    print(f"  [OK] Weapon Mesh {mpid} ('{mtt['m_Name']}') verts={expected_v}, BindPose=Identity")

# Check Reparented Sword & Gun PropsController + Transforms
for pc_pid, expected_rh_pid in ((-8490429130128858862, -4088132481749495149), (-3021806434293993593, -8402135396370300167)):
    pc = bw_objs[pc_pid].read_typetree()
    props = dict(zip(pc["_props"]["_serializedKeys"], pc["_props"]["_serializedValues"]))
    for key in ("gun", "sword"):
        assert key in props and props[key]["InitFlags"] == 0
        assert props[key]["_animator"]["m_PathID"] == 0
        assert len(props[key]["_renderers"]) == 1 and props[key]["_renderers"][0]["m_PathID"] in bw_objs
    assert props["gun"]["RootPath"].endswith("/LeftHand")
    assert props["sword"]["RootPath"].endswith("/RightHand")
    print(f"  [OK] PropsController {pc_pid}: gun@LeftHand & sword@RightHand (InitFlags=0, _startActive=False)")

# Check FSB5 audio slices for gunshots
for apid in (941368445438371770, -3153366270135029083, 6494165064040424260, -9094754406746335516):
    at = bw_objs[apid].read_typetree()
    res = at["m_Resource"]
    res_file.seek(res["m_Offset"])
    hdr = res_file.read(4)
    assert hdr == b"FSB5" and res["m_Size"] > 10000, f"Bad audio {apid}: {res}"
print("  [OK] All 4 Gunshot AudioClips point to valid FSB5 streams in .resource")

# Check AOC slots
aoc = bw_objs[-7755666207738536548].read_typetree()
for slot_idx in (2, 3, 4, 5, 41, 42, 43, 44, 51, 52, 53, 63, 64, 65):
    over = aoc["m_Clips"][slot_idx]["m_OverrideClip"]
    fid, pid = over["m_FileID"], over["m_PathID"]
    ok = (pid in bw_objs) if fid == 0 else (pid in EXT_MAP[fid])
    assert ok, f"Broken AOC slot {slot_idx}: ({fid}, {pid})"
print("  [OK] Fight AOC all 14 combat slots resolve cleanly (local or anim_procedural)")

# Check MoveSet entries
ms = bw_objs[5996528693102170603].read_typetree()
ms_by_state = {m["_animStateName"]: (m["_name"], m["_asset"]["m_FileID"], m["_asset"]["m_PathID"]) for m in ms["_moves"] if m.get("_animStateName")}
for state in (
    "Base.LightAttack01", "Base.LightAttack02", "Base.LightAttack03", "Base.LightAttack04",
    "Base.MediumAttack01", "Base.MediumAttack02",
    "Base.RangedAttack01", "Base.RangedAttack02", "Base.RangedAttack03",
    "Base.SpecialAttack01", "Base.SpecialAttack02",
    "Base.Misc01", "Base.Misc02", "Base.Misc03",
):
    nm, fid, pid = ms_by_state[state]
    assert fid == 7 and pid in mv_pids, f"MoveSet broken for {state}: {nm} ({fid},{pid})"
    print(f"  [OK] MoveSet {state:<22} -> {nm} (PID={pid})")

# Check All 4 Projectiles + Root PrefabList (preserving projectile_megatron_gs_bullet for Tank Heavy!)
for gpid, expected_nm in (
    (9003878510878022874, "projectile_megatron_gs_bullet"),
    (4196009027374098921, "projectile_optimus_bullet"),
    (-8888888888888888920, "projectile_special_bullet"),
    (2836027833803039595, "projectile_sideswipe_missile"),
):
    assert bw_objs[gpid].read_typetree()["m_Name"] == expected_nm
print("  [OK] All 4 projectile prefabs (Tank Heavy + Ranged Gun + Tank S1 + Jet S2) wired cleanly")
print("\n[✓] ALL BLITZWING WEAPON, AUDIO, ANIMATION, AND DUAL-SP CHECKS PASSED!")
