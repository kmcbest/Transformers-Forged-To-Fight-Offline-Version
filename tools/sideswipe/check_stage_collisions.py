import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import deque
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

env_ss = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf_ss = list(env_ss.assets)[0]

env_op = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))
sf_op = list(env_op.assets)[0]

env_ch = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "cheetor_bw_transmetal_odr" / "cheetor_bw_transmetal.assetbundle"))
sf_ch = list(env_ch.assets)[0]

def iter_pptrs(node):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            yield node
        else:
            for v in node.values():
                yield from iter_pptrs(v)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from iter_pptrs(x)

def collect_closure(sf, root_pids):
    visited = set()
    queue = deque(root_pids)
    visited.update(root_pids)
    while queue:
        cur = queue.popleft()
        obj = sf.objects.get(cur)
        if not obj: continue
        try:
            tree = obj.read_typetree()
        except:
            continue
        for pptr in iter_pptrs(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if fid == 0 and tpid != 0 and tpid not in visited:
                visited.add(tpid)
                queue.append(tpid)
    return visited

OP_STAGE_ROOT = 3256447252977910551
op_stage_pids = collect_closure(sf_op, [OP_STAGE_ROOT])

print(f"Optimus Stage PIDs count: {len(op_stage_pids)}")
# Check collisions with Sideswipe
collisions = op_stage_pids & set(sf_ss.objects.keys())
print(f"Collisions between Optimus Stage and Sideswipe bundle: {len(collisions)}")
for c in collisions:
    o_ss = sf_ss.objects[c]
    o_op = sf_op.objects[c]
    print(f"  Collision PID={c}: SS={o_ss.type.name} (class={o_ss.class_id}), OP={o_op.type.name} (class={o_op.class_id})")

# Cheetor clips
cheetor_m2_pid = -1929738649458782990
cheetor_s1_pid = 868105726138923071
print(f"Cheetor M2 in SS: {cheetor_m2_pid in sf_ss.objects}")
print(f"Cheetor S1 in SS: {cheetor_s1_pid in sf_ss.objects}")
