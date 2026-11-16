import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import deque
import json
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

print("=== 1. Checking Brawl Bundle Integrity ===")
env_b = UnityPy.load(str(BRAWL_BUNDLE))
sf_b = list(env_b.assets)[0]

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

dangling = []
oor = []
for pid, obj in sf_b.objects.items():
    try:
        tt = obj.read_typetree()
    except Exception as e:
        print(f"  [READ ERROR] pid={pid} type={obj.type.name}: {e}")
        continue
    for p in iter_pptrs(tt):
        fid, tpid = p.get("m_FileID", 0), p.get("m_PathID", 0)
        if tpid == 0:
            continue
        if fid == 0 and tpid not in sf_b.objects:
            dangling.append((pid, obj.type.name, tpid))
        elif fid > len(sf_b.externals) or fid < 0:
            oor.append((pid, obj.type.name, fid, tpid))

print(f"Dangling local PPtrs (FileID=0 not in objects): {len(dangling)}")
for x in dangling[:10]:
    print(" ", x)

print(f"Out of range external PPtrs: {len(oor)}")
for x in oor[:10]:
    print(" ", x)

print("\n=== 2. Checking Stream Data / Resources ===")
bad_streams = []
for pid, obj in sf_b.objects.items():
    try:
        tt = obj.read_typetree()
    except:
        continue
    sd = tt.get("m_StreamData")
    if isinstance(sd, dict) and sd.get("size", 0) > 0:
        path = sd.get("path", "")
        bad_streams.append((pid, obj.type.name, tt.get("m_Name"), path, sd.get("size")))
    res = tt.get("m_Resource")
    if isinstance(res, dict) and res.get("m_Size", 0) > 0:
        src = res.get("m_Source", "")
        bad_streams.append((pid, obj.type.name, tt.get("m_Name"), src, res.get("m_Size")))

print(f"Stream / Resource references: {len(bad_streams)}")
for s in bad_streams:
    print(" ", s)

print("\n=== 3. Checking AssetBundle Container & PreloadTable ===")
ab_tree = next(o.read_typetree() for o in sf_b.objects.values() if o.type.name == "AssetBundle")
pt = [(p["m_FileID"], p["m_PathID"]) for p in ab_tree.get("m_PreloadTable", [])]
print(f"PreloadTable entries: {len(pt)}")
for cname, cinfo in ab_tree.get("m_Container", []):
    rpid = cinfo["asset"]["m_PathID"]
    idx, sz = cinfo["preloadIndex"], cinfo["preloadSize"]
    print(f"  Container '{cname}': asset_pid={rpid}, preloadIndex={idx}, preloadSize={sz}")
