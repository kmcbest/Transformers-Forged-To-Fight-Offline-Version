import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

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

all_pids = set(sf.objects.keys())
dangling = []
for pid, obj in sf.objects.items():
    try:
        tt = obj.read_typetree()
    except Exception as e:
        print(f"Error reading typetree for PID={pid} ({obj.type.name}): {e}")
        continue
    for pptr in iter_pptrs_in_tree(tt):
        fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
        if fid == 0 and tpid != 0 and tpid not in all_pids:
            dangling.append((pid, obj.type.name, tpid))

print(f"Total objects: {len(sf.objects)}")
print(f"Total dangling internal PPtrs: {len(dangling)}")
for pid, tname, tpid in dangling[:20]:
    print(f"  Obj PID={pid} ({tname}) -> MISSING PID={tpid}")
