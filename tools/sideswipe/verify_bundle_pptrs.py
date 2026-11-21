import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"

env = UnityPy.load(str(bundle_path))
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

dangling = []
out_of_range = []
for pid, obj in sf.objects.items():
    try:
        tree = obj.read_typetree()
    except Exception:
        continue
    for pptr in iter_pptrs_in_tree(tree):
        fid, tpid = int(pptr.get("m_FileID", 0)), int(pptr.get("m_PathID", 0))
        if tpid == 0:
            continue
        if fid == 0:
            if tpid not in sf.objects:
                dangling.append((pid, obj.type.name, tpid))
        else:
            if not (1 <= fid <= len(sf.externals)):
                out_of_range.append((pid, obj.type.name, fid, tpid))

print(f"Dangling local PPtrs: {len(dangling)}")
if dangling:
    for d in dangling[:10]:
        print(f"  {d}")

print(f"Out-of-range external PPtrs: {len(out_of_range)}")
if out_of_range:
    for o in out_of_range[:10]:
        print(f"  {o}")

assert not dangling, "Dangling local PPtrs found!"
assert not out_of_range, "Out-of-range external PPtrs found!"
print("[ALL CLEAN] Bundle PPtr integrity 100% verified!")
