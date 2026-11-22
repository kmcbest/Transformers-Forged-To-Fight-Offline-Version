import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path
import UnityPy

ROOT = Path(r"e:\Agent\TFTF-blender")
BUNDLES = [
    "assets_redeco/onslaught_gs.assetbundle",
    "assets_redeco/brawl_gs.assetbundle",
    "assets_redeco/vortex_gs.assetbundle",
]

def scan_pptrs(obj):
    if isinstance(obj, dict):
        if set(obj.keys()) == {"m_FileID", "m_PathID"}:
            yield int(obj["m_FileID"]), int(obj["m_PathID"])
        else:
            for v in obj.values():
                yield from scan_pptrs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from scan_pptrs(v)

for rel in BUNDLES:
    p = ROOT / rel
    env = UnityPy.load(str(p))
    sf = list(env.assets)[0]
    head_bytes = subprocess.check_output(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"])
    env_head = UnityPy.load(head_bytes)
    sf_head = list(env_head.assets)[0]

    # 1. script_types & MonoBehaviour m_Script parity
    st_cur = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf.script_types]
    st_head = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in sf_head.script_types]
    assert st_cur == st_head, f"{rel} script_types mismatch!"
    for pid, o in sf.objects.items():
        if o.type.name == "MonoBehaviour":
            tt_mb = o.read_typetree()
            ms = tt_mb.get("m_Script", {})
            if "m_FileID" in ms and "m_PathID" in ms and hasattr(o, "serialized_type"):
                idx = o.serialized_type.script_type_index
                if 0 <= idx < len(sf.script_types):
                    ident = sf.script_types[idx]
                    assert (ms["m_FileID"], ms["m_PathID"]) == (ident.local_serialized_file_index, ident.local_identifier_in_file), f"{rel} MonoBehaviour {pid} script index mismatch!"

    # 2. Local PPtrs valid
    bad_local = []
    for o in sf.objects.values():
        if o.type.name in ("AssetBundle", "PreloadData"):
            continue
        tt = o.read_typetree()
        for fid, pid in scan_pptrs(tt):
            if fid == 0 and pid != 0 and pid not in sf.objects:
                bad_local.append((o.path_id, o.type.name, pid))
    assert not bad_local, f"{rel} dangling local PPtrs: {bad_local[:5]}"

    # 3. PreloadTable contiguous & ascending check
    ab_tt = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
    pt = ab_tt.get("m_PreloadTable", [])
    cursor = 0
    cnames = []
    containers = sorted(ab_tt.get("m_Container", []), key=lambda kv: int(kv[1]["preloadIndex"]))
    for cname, cinfo in containers:
        cnames.append(cname)
        pidx, psize = int(cinfo["preloadIndex"]), int(cinfo["preloadSize"])
        assert pidx == cursor, f"{rel} {cname} non-contiguous preloadIndex {pidx} != {cursor}"
        cursor += psize
        seen_fids, prev_fid, prev_pid = set(), None, None
        for entry in pt[pidx : pidx + psize]:
            fid, pid = int(entry["m_FileID"]), int(entry["m_PathID"])
            if fid != prev_fid:
                assert fid not in seen_fids, f"{rel} {cname} split FileID {fid}"
                seen_fids.add(fid)
                prev_fid, prev_pid = fid, pid
            else:
                assert pid > prev_pid, f"{rel} {cname} unsorted PathID in FileID {fid}: {prev_pid} -> {pid}"
                prev_pid = pid
    print(f"[PASS] {rel}: size={p.stat().st_size:,} B, objects={len(sf.objects)}, script_types={len(sf.script_types)}, containers={cnames}, bad_local=0")
