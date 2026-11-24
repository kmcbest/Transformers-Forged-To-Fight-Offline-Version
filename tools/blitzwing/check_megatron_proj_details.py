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

for pid in (7216954881528309562, -4642064524079818382, -5508172462261296737, 6775277914025461342):
    t = objs[pid].read_typetree()
    go = objs[t["m_GameObject"]["m_PathID"]].read_typetree()
    print(f"PrefabList {pid} GO={go['m_Name']} keys={list(t.keys())} len={len(t.get('PrefabList', []))}")
    for e in t.get("PrefabList", [])[:6]:
        print(" ", e)

for pid in (4196009027374098921, 9003878510878022874, 2836027833803039595):
    go = objs[pid].read_typetree()
    print(f"\nProjectile GO {pid} '{go['m_Name']}' comps:")
    for c in go["m_Component"]:
        cp = c["component"]["m_PathID"]
        tp = objs[cp].type.name
        print(f"  {tp} PID={cp}")
        if tp == "MonoBehaviour":
            tt = objs[cp].read_typetree()
            if "_moves" in tt:
                print("    _moves:", tt["_moves"])
            elif "CollisionPointOffset" in tt:
                print("    cfg:", {k: v for k, v in tt.items() if k in ("CollisionPointOffset", "MoveToPlayOnFire", "MoveToPlayOnExplode")})

# Also check Showcase MoveSet & Combat MoveSet & mace/staticCannon GOs
for pid in (-7375623541015776277, 1109389691721735991, -6258551087734041547, 74419346676817846):
    go = objs[pid].read_typetree()
    print(f"Weapon GO {pid} '{go['m_Name']}' m_IsActive={go['m_IsActive']} comps={[(objs[c['component']['m_PathID']].type.name, c['component']['m_PathID']) for c in go['m_Component']]}")
