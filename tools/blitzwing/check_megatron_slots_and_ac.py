import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

MEGA = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(MEGA))
objs = {o.path_id: o for o in env.objects}

# 1. Inspect Megatron Fight AOC (-7755666207738536548) slots
aoc = objs[-7755666207738536548].read_typetree()
print("=== Megatron Fight AOC m_Clips ===")
for i, c in enumerate(aoc["m_Clips"]):
    orig = c["m_OriginalClip"]
    over = c["m_OverrideClip"]
    def cname(p):
        fid, pid = p["m_FileID"], p["m_PathID"]
        if pid == 0: return "None"
        if fid == 0 and pid in objs: return objs[pid].read_typetree().get("m_Name", "?")
        return f"ext({fid},{pid})"
    if i in (2,3,4,5,41,42,43,44,51,52,53,63,64,65):
        print(f"  slot {i:2d}: orig=({orig['m_FileID']},{orig['m_PathID']}) [{cname(orig)}] | over=({over['m_FileID']},{over['m_PathID']}) [{cname(over)}]")

# 2. Check target slots & unused local clips we plan to overwrite:
target_clip_pids = [
    3447898299160786076,   # Megatron L2
    80445849579449578,     # Megatron L3
    7166247695725661904,   # Megatron L4
    5574244196002706121,   # Megatron M1
    3299789870907881362,   # Megatron M2
    -7039854538955176447,  # Megatron S1
    93796867180898313,     # Megatron S2
    -4759913177061412663,  # Megatron S1 mace -> reuse for Windblade S1
]
print("\n=== Target Megatron AnimationClip Slots ===")
for pid in target_clip_pids:
    t = objs[pid].read_typetree()
    print(f"  {pid}: '{t['m_Name']}' len={t['m_MuscleClip']['m_StopTime']:.3f}")

# 3. Check CHAR_FIGHT_AC (-6923321525341018075) Base Layer states for SpecialAttack01/02 & Misc02/03
ac = objs[-6923321525341018075].read_typetree()
tos = ac["m_TOS"]
# Note m_TOS is list of [hash, name] or dict
print("\n=== CHAR_FIGHT_AC State Hashes check ===")
tos_map = {e["first"]: e["second"] for e in tos} if isinstance(tos[0], dict) else dict(tos)
sm = ac["m_Controller"]["m_StateMachineArray"][0]
sm_data = sm.get("data", sm)
for idx, st in enumerate(sm_data["m_StateConstantArray"]):
    d = st.get("data", st)
    nm = tos_map.get(d["m_NameID"], str(d["m_NameID"]))
    if any(k in nm for k in ("SpecialAttack", "Misc0", "HeavyAttack", "RangedAttack")):
        print(f"  idx={idx:2d} name='{nm}' id={d['m_NameID']} ik={d['m_IKOnFeet']} tag={d['m_TagID']} speed={d['m_Speed']} trans={len(d['m_TransitionConstantArray'])}")

print("\n=== Combat MoveSet 5996528693102170603 existing special/ranged/melee entries ===")
ms = objs[5996528693102170603].read_typetree()
for i, m in enumerate(ms["_moves"]):
    print(f"  [{i:2d}] name={m['_name']} animState={m['_animStateName']} asset=({m['_asset']['m_FileID']},{m['_asset']['m_PathID']})")

print("\n=== PrefabLists in Megatron Showcase & Combat ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        if "_prefabs" in t:
            go = objs[t["m_GameObject"]["m_PathID"]].read_typetree()
            print(f"  PrefabList GO={go['m_Name']} PID={o.path_id} count={len(t['_prefabs'])} items={[(e['Prefab']['m_FileID'], e['Prefab']['m_PathID'], e.get('Amount')) for e in t['_prefabs']]}")
