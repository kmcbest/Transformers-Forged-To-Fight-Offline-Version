import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
from collections import deque

ROOT = Path(r"E:\Agent\TFTF-blender")
env_op = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))
sf_op = list(env_op.assets)[0]

def iter_pptrs_in_tree(node):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            yield node
        else:
            for v in node.values():
                yield from iter_pptrs_in_tree(v)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from iter_pptrs_in_tree(x)

def collect_closure(sf, root_pids):
    visited = set()
    queue = deque(root_pids)
    visited.update(root_pids)
    while queue:
        cur = queue.popleft()
        obj = sf.objects.get(cur)
        if obj is None:
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        for pptr in iter_pptrs_in_tree(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if fid == 0 and tpid != 0 and tpid not in visited:
                visited.add(tpid)
                queue.append(tpid)
    return visited

stage_pids = collect_closure(sf_op, [3256447252977910551])
print(f"Optimus SP3 Stage Closure: {len(stage_pids)} objects")
type_counts = {}
for pid in stage_pids:
    obj = sf_op.objects[pid]
    type_counts[obj.type.name] = type_counts.get(obj.type.name, 0) + 1
print("Type counts in stage closure:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")

# Check any local AnimationClips or MonoBehaviours in stage
for pid in stage_pids:
    obj = sf_op.objects[pid]
    if obj.type.name == "MonoBehaviour":
        tt = obj.read_typetree()
        if "jSONData" in tt:
            print(f"MatineeData PID={pid}: name={tt.get('m_Name')}")
    elif obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        print(f"AnimationClip in stage PID={pid}: {tt.get('m_Name')}")
