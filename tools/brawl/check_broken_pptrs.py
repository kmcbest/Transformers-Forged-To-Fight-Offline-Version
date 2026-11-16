import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]

existing_pids = set(sf.objects.keys())
externals_len = len(sf.externals)

broken_refs = []

def check_pptrs(obj_pid, obj_type, node, path=""):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            fid = node["m_FileID"]
            pid = node["m_PathID"]
            if pid != 0:
                if fid == 0 and pid not in existing_pids:
                    broken_refs.append((obj_pid, obj_type, path, fid, pid, "Internal PID not found"))
                elif fid > externals_len:
                    broken_refs.append((obj_pid, obj_type, path, fid, pid, f"FileID {fid} > externals count {externals_len}"))
        else:
            for k, v in node.items():
                check_pptrs(obj_pid, obj_type, v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for idx, item in enumerate(node):
            check_pptrs(obj_pid, obj_type, item, f"{path}[{idx}]")

for pid, obj in sf.objects.items():
    try:
        tt = obj.read_typetree()
        check_pptrs(pid, obj.type.name, tt)
    except Exception as e:
        broken_refs.append((pid, obj.type.name, "read_typetree", 0, 0, f"Exception: {e}"))

print(f"Total objects scanned: {len(sf.objects)}")
print(f"Broken references found: {len(broken_refs)}")
for br in broken_refs[:30]:
    print(" ", br)
