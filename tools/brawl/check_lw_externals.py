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

def get_lw_externals(bundle_path, root_name):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    ext_names = {i+1: ext.name for i, ext in enumerate(sf.externals)}
    
    # find root
    root_pid = None
    for pid, obj in sf.objects.items():
        if obj.type.name == "GameObject":
            tt = obj.read_typetree()
            if tt["m_Name"] == root_name:
                root_pid = pid
                break
    
    # collect closure
    visited = set()
    queue = deque([root_pid])
    visited.add(root_pid)
    externals_found = []
    
    while queue:
        cur = queue.popleft()
        obj = sf.objects.get(cur)
        if not obj:
            continue
        try:
            tt = obj.read_typetree()
        except:
            continue
        for pptr in iter_pptrs_in_tree(tt):
            fid = int(pptr.get("m_FileID", 0))
            tpid = int(pptr.get("m_PathID", 0))
            if fid == 0 and tpid != 0:
                if tpid not in visited:
                    visited.add(tpid)
                    queue.append(tpid)
            elif fid > 0:
                externals_found.append((cur, obj.type.name, fid, ext_names.get(fid, "UNKNOWN"), tpid))
                
    return externals_found

br_exts = get_lw_externals(BRAWL_BUNDLE, "brawl_gs_lw")
meg_exts = get_lw_externals(MEG_BUNDLE, "Megatron_Cin_ROTF_lw")

print(f"Brawl _lw external references ({len(br_exts)}):")
for cur, tname, fid, ename, tpid in br_exts:
    print(f"  From {cur} ({tname}) -> FileID={fid} ({ename}), PathID={tpid}")

print(f"\nMegatron _lw external references ({len(meg_exts)}):")
for cur, tname, fid, ename, tpid in meg_exts:
    print(f"  From {cur} ({tname}) -> FileID={fid} ({ename}), PathID={tpid}")
