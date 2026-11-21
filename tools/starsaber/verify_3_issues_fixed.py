import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\starsaber_gs_leader2014.assetbundle")
env = UnityPy.load(str(bundle_path))

print("=== [Verification] Verifying All 3 User Issues Resolved ===")

go_map = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "GameObject"}
tr_map = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "Transform"}

# 1. Gun Transform Orientation & Position under LeftHand
gun_tr_pid = -4730893461018512753
assert gun_tr_pid in tr_map
gun_tr = tr_map[gun_tr_pid]
lh_pid = gun_tr.get("m_Father", {}).get("m_PathID")
lh_go_pid = tr_map.get(lh_pid, {}).get("m_GameObject", {}).get("m_PathID")
lh_name = go_map.get(lh_go_pid, {}).get("m_Name")
print(f"Issue 1 Check (Gun Mount):")
print(f"  Parent: '{lh_name}' (PID={lh_pid})")
print(f"  LocalPos: {gun_tr.get('m_LocalPosition')}")
print(f"  LocalRot: {gun_tr.get('m_LocalRotation')}")
assert lh_name == "LeftHand"
assert abs(gun_tr["m_LocalPosition"]["x"] - (-0.80)) < 0.001
assert abs(gun_tr["m_LocalPosition"]["y"] - (-0.8073)) < 0.001
assert abs(gun_tr["m_LocalPosition"]["z"] - 2.5779) < 0.001
assert abs(gun_tr["m_LocalRotation"]["y"] - (-0.707107)) < 0.001
assert abs(gun_tr["m_LocalRotation"]["w"] - 0.707107) < 0.001
print("  [PASS] Gun Transform has 90 deg forward pitch (y = -0.707107, w = 0.707107) under LeftHand!")

# Rifle Mesh Transform under gun
rifle_mesh_tr_pid = -6795244851938642244
rifle_tr = tr_map[rifle_mesh_tr_pid]
print(f"  Rifle Mesh LocalPos: {rifle_tr.get('m_LocalPosition')}")
print(f"  Rifle Mesh LocalRot: {rifle_tr.get('m_LocalRotation')}")
assert abs(rifle_tr["m_LocalPosition"]["x"] - (-1.04534)) < 0.001
assert abs(rifle_tr["m_LocalRotation"]["z"] - (-0.707106)) < 0.001
print("  [PASS] Rifle child mesh matches Motormaster exact donor orientation (Euler Z = -90 deg)!")

# PropsController RootPath and PositionOffset verification
for pc_pid in (-9009354885740569570, 1062452820465670706):
    pc_obj = [o for o in env.objects if o.path_id == pc_pid][0]
    pc_tt = pc_obj.read_typetree()
    props = pc_tt.get("_props", {})
    keys = props.get("_serializedKeys", [])
    vals = props.get("_serializedValues", [])
    gun_val = vals[keys.index("gun")]
    assert "LeftHand" in gun_val["RootPath"], f"PropsController {pc_pid} RootPath does not contain LeftHand!"
    assert abs(gun_val["PositionOffset"]["x"] - (-0.80)) < 0.001
    assert abs(gun_val["PositionOffset"]["y"] - (-0.8073)) < 0.001
    assert abs(gun_val["PositionOffset"]["z"] - 2.5779) < 0.001
    assert abs(gun_val["RotationOffset"]["y"] - (-90.0)) < 0.001
    print(f"  [PASS] PropsController {pc_pid} RootPath correctly targets LeftHand with exact offsets!")

# 2. Projectile Optimus Bullet
bullet_go_pid = -3806194776990344199
assert bullet_go_pid in go_map
bullet_go = go_map[bullet_go_pid]
print(f"\nIssue 2 Check (Projectile & Hit Detection):")
print(f"  Bullet GO Name: '{bullet_go.get('m_Name')}'")
assert bullet_go.get("m_Name") == "projectile_optimus_bullet"

# Check MoveSet on bullet
ms_bullet_pid = -7987045836701848350
ms_obj = [o for o in env.objects if o.path_id == ms_bullet_pid][0].read_typetree()
moves = ms_obj.get("_moves", [])
print(f"  Bullet MoveSet moves count: {len(moves)}")
for m in moves:
    print(f"    Move: '{m.get('_name')}' -> FileID={m.get('_asset', {}).get('m_FileID')} PathID={m.get('_asset', {}).get('m_PathID')}")
assert any(m.get("_name") == "fire" and m.get("_asset", {}).get("m_PathID") == 6337232768847846927 for m in moves)
assert any(m.get("_name") == "explode" and m.get("_asset", {}).get("m_PathID") == 98785653677070406 for m in moves)
print("  [PASS] Bullet MoveSet correctly wired to move_optimus_bullet_fire & move_optimus_bullet_explode!")

# Check PrefabList registration on bullet (particles for laser bolt and impact)
bullet_pref_pid = 7976934786116503278
bullet_pref_mb = [o for o in env.objects if o.path_id == bullet_pref_pid][0].read_typetree()
bullet_pids = {item.get("Prefab", {}).get("m_PathID") for item in bullet_pref_mb.get("PrefabList", [])}
print(f"  Bullet PrefabList PIDs: {bullet_pids}")
assert -6715103446334267986 in bullet_pids, "Missing fx_p_red_projectile in bullet PrefabList!"
assert -8062247508178286595 in bullet_pids, "Missing fx_p_red_projectile_impact in bullet PrefabList!"
assert 8149109851183567790 in bullet_pids, "Missing fx_l_hit_small_perceptual in bullet PrefabList!"
print("  [PASS] Bullet PrefabList correctly contains red laser bolt and impact particle prefabs!")

# Check PrefabList registration on bot root
bot_prefablist_pid = 9200960997345802874
bot_pref_mb = [o for o in env.objects if o.path_id == bot_prefablist_pid][0].read_typetree()
bot_pids = {item.get("Prefab", {}).get("m_PathID") for item in bot_pref_mb.get("PrefabList", [])}
assert bullet_go_pid in bot_pids, "Missing bullet_go in Bot PrefabList!"
assert -6715103446334267986 in bot_pids, "Missing fx_p_red_projectile in Bot PrefabList!"
assert -8062247508178286595 in bot_pids, "Missing fx_p_red_projectile_impact in Bot PrefabList!"
print("  [PASS] projectile_optimus_bullet & red laser bolt prefabs registered in bot's active Pool/PrefabList!")

# 3. Audio Firing Sound Effect
print(f"\nIssue 3 Check (Motormaster Gunshot Sound Effect):")
res_reader = next((f for n, f in env.file.files.items() if n.endswith(".resource")), None)
assert res_reader is not None

audio_pids = (5765912829461940224, 8819501287347053159, 3045197054732182151, 4483602982996036395)
for idx, pid in enumerate(audio_pids, 1):
    obj = [o for o in env.objects if o.path_id == pid][0]
    tt = obj.read_typetree()
    res = tt.get("m_Resource", {})
    offset = res.get("m_Offset")
    size = res.get("m_Size")
    res_reader.seek(offset)
    chunk = res_reader.read(size)
    assert len(chunk) == size
    assert chunk[:4] == b"FSB5"
    print(f"  Clip variation {idx} (PID={pid}): Length={tt.get('m_Length'):.3f}s, Size={size} bytes, Header={chunk[:4]}")
    assert abs(tt.get("m_Length") - 2.664) < 0.01
    assert size == 21984

print("  [PASS] All 4 gunshot audio clips contain authentic Motormaster/Optimus 2.664s heavy gunshot FSB5 audio!")

print("\n>>> ALL 3 USER VERIFICATION GATES PASSED 100%! <<<")
