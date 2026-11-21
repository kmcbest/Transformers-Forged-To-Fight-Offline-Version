import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import deque
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"

env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

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
    all_pptrs = set()
    queue = deque()
    for r in root_pids:
        if r and r in sf.objects and r not in visited:
            all_pptrs.add((0, r))
            visited.add(r)
            queue.append(r)
    while queue:
        cur = queue.popleft()
        obj = sf.objects.get(cur)
        if obj is None:
            continue
        try:
            tree = obj.read_typetree()
        except:
            continue
        for pptr in iter_pptrs(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if tpid == 0:
                continue
            all_pptrs.add((fid, tpid))
            if fid == 0 and tpid not in visited:
                if tpid in sf.objects:
                    visited.add(tpid)
                    queue.append(tpid)
    return visited, all_pptrs

ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
ab_tree = ab_obj.read_typetree()

live_pids = set()
for cname, cinfo in ab_tree.get("m_Container", []):
    rpid = int(cinfo["asset"]["m_PathID"])
    loc, _ = collect_closure(sf, [rpid])
    live_pids |= loc

all_monoscripts = {pid for pid, o in sf.objects.items() if o.class_id == 115}
unreachable = set(sf.objects.keys()) - live_pids - all_monoscripts - {ab_obj.path_id}
print(f"Total objects in SS bundle: {len(sf.objects)}")
print(f"Live reachable objects: {len(live_pids)}")
print(f"MonoScripts: {len(all_monoscripts)}")
print(f"Unreachable objects: {len(unreachable)}")
