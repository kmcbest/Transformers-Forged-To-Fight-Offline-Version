import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import deque
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

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
    all_pptrs = set()
    queue = deque()
    for r in root_pids:
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
        for pptr in iter_pptrs_in_tree(tree):
            fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
            if tpid == 0:
                continue
            all_pptrs.add((fid, tpid))
            if fid == 0 and tpid not in visited:
                visited.add(tpid)
                queue.append(tpid)
    return visited, all_pptrs

ab_tree = next(o.read_typetree() for o in sf.objects.values() if o.type.name == "AssetBundle")
pt = [(p["m_FileID"], p["m_PathID"]) for p in ab_tree.get("m_PreloadTable", [])]

for cname, cinfo in ab_tree.get("m_Container", []):
    rpid = cinfo["asset"]["m_PathID"]
    idx, sz = cinfo["preloadIndex"], cinfo["preloadSize"]
    sl = pt[idx:idx+sz]
    _, expected_set = collect_closure(sf, [rpid])
    sl_set = set(sl)
    missing = expected_set - sl_set
    print(f"\nMissing in '{cname}':")
    for fid, pid in sorted(missing):
        ext_name = sf.externals[fid - 1].path if 1 <= fid <= len(sf.externals) else "LOCAL"
        print(f"  FileID={fid} ({ext_name}), PathID={pid}")
