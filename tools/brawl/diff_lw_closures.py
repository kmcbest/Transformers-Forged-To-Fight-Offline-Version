import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
from collections import deque

ROOT = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

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

env_meg = UnityPy.load(str(MEG_BUNDLE))
sf_meg = list(env_meg.assets)[0]
meg_lw_pid = 7253228804562187563
meg_vis, meg_pptrs = collect_closure(sf_meg, [meg_lw_pid])

env_br = UnityPy.load(str(BRAWL_BUNDLE))
sf_br = list(env_br.assets)[0]
br_lw_pid = 7253228804562187563
br_vis, br_pptrs = collect_closure(sf_br, [br_lw_pid])

print(f"Megatron _lw closure: {len(meg_vis)} internal objects, {len(meg_pptrs)} total pptrs")
print(f"Brawl _lw closure: {len(br_vis)} internal objects, {len(br_pptrs)} total pptrs")

diff_meg = meg_pptrs - br_pptrs
print(f"\nPptrs in Megatron _lw but NOT in Brawl _lw ({len(diff_meg)}):")
for fid, pid in sorted(diff_meg):
    obj = sf_meg.objects.get(pid)
    tname = obj.type.name if obj else "EXTERNAL"
    print(f"  FileID={fid}, PathID={pid} ({tname})")

diff_br = br_pptrs - meg_pptrs
print(f"\nPptrs in Brawl _lw but NOT in Megatron _lw ({len(diff_br)}):")
for fid, pid in sorted(diff_br):
    obj = sf_br.objects.get(pid)
    tname = obj.type.name if obj else "EXTERNAL"
    print(f"  FileID={fid}, PathID={pid} ({tname})")
