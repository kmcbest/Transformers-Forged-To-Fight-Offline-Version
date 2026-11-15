import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))
obj_map = {o.path_id: o for o in env.objects}

smr = obj_map[3992037002325232027].read_typetree()
go_pid = smr["m_GameObject"]["m_PathID"]
go = obj_map[go_pid].read_typetree()
root_bone_tr_pid = smr["m_RootBone"]["m_PathID"]
root_bone_tr = obj_map[root_bone_tr_pid].read_typetree()
root_bone_go = obj_map[root_bone_tr["m_GameObject"]["m_PathID"]].read_typetree()
print(f"Jet SMR GO: '{go['m_Name']}' (PID {go_pid})")
print(f"Jet RootBone: '{root_bone_go['m_Name']}' (Tr PID {root_bone_tr_pid})")

curr = root_bone_tr_pid
path = []
while curr in obj_map:
    tr = obj_map[curr].read_typetree()
    tr_go = obj_map[tr["m_GameObject"]["m_PathID"]].read_typetree()
    path.append(tr_go["m_Name"])
    curr = tr["m_Father"]["m_PathID"]

print("RootBone path to root:", " / ".join(reversed(path)))

# Check the Animator on cannon
for c in obj_map[-2922891105374208445].read_typetree()["m_Component"]:
    cid = c["component"]["m_PathID"]
    if cid in obj_map and obj_map[cid].type.name == "Animator":
        atr = obj_map[cid].read_typetree()
        print(f"Cannon Animator: Avatar PID={atr.get('m_Avatar')}")
