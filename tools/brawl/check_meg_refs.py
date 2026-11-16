import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))
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

counts = {}
for obj in sf.objects.values():
    try:
        tt = obj.read_typetree()
    except:
        continue
    for p in iter_pptrs(tt):
        fid = p.get("m_FileID", 0)
        counts[fid] = counts.get(fid, 0) + 1

print("FileID reference counts in megatron_cin_rotf:")
for fid, count in sorted(counts.items()):
    ext_name = sf.externals[fid - 1].path if 1 <= fid <= len(sf.externals) else "LOCAL" if fid == 0 else "INVALID"
    print(f"  FileID {fid}: {count} refs -> {ext_name}")
