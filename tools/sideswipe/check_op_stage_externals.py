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
    all_pptrs = set()
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
            if tpid != 0:
                all_pptrs.add((fid, tpid))
            if fid == 0 and tpid != 0 and tpid not in visited:
                visited.add(tpid)
                queue.append(tpid)
    return visited, all_pptrs

OP_STAGE_ROOT = 3256447252977910551
_, all_pptrs = collect_closure(sf_op, [OP_STAGE_ROOT])

ext_fids = {fid for fid, pid in all_pptrs if fid > 0}
print(f"External FileIDs in Optimus Stage: {ext_fids}")
for fid in ext_fids:
    ext_path = sf_op.externals[fid - 1].path if fid <= len(sf_op.externals) else "UNKNOWN"
    print(f"  Optimus FileID {fid}: {ext_path}")

print("\nSideswipe Externals:")
for idx, ext in enumerate(sf_ss.externals, 1):
    print(f"  Sideswipe FileID {idx}: {ext.path}")
