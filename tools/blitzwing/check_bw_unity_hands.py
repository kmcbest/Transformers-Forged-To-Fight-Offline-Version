import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy
from inspect_sword_space_and_fx import q_to_m3, bp_to_m4, m4_mul, m4_pt

BW_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(BW_BUNDLE))
objs = {o.path_id: o for o in env.objects}

# Check RightHand (-8402135396370300167) and LeftHand (-9072195252855702323) world matrices in T-pose / Avatar / BindPose!
# Actually look at Mesh_0 BindPose for LeftHand and RightHand on cha_blitzwing_gs_00!
# Let's inspect RightProp (TR=795564558934611553), LeftProp (TR=-6348088967389488120) and Windblade Sword matrix M_wb!
def chain_to_root(tr_pid):
    chain = []
    cur = tr_pid
    while cur and cur in objs:
        t = objs[cur].read_typetree()
        go = objs[t["m_GameObject"]["m_PathID"]].read_typetree()
        chain.append((go["m_Name"], cur, t))
        cur = t["m_Father"]["m_PathID"]
    chain.reverse()
    M = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    from inspect_sword_space_and_fx import tr_to_m4
    for nm, pid, t in chain:
        M = m4_mul(M, tr_to_m4(t))
    return M, chain

for label, pid in [("Combat LeftHand", -9072195252855702323), ("Combat RightHand", -8402135396370300167),
                   ("Combat LeftProp", -6717427732617845385), ("Combat RightProp", 795564558934611553)]:
    M, ch = chain_to_root(pid)
    print(f"\n=== {label} (TR={pid}) ===")
    print("  path:", " -> ".join(c[0] for c in ch))
    print("  World Matrix:")
    for r in M:
        print("   ", [round(x, 4) for x in r])
