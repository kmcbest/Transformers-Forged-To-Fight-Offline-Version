import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy
import zlib

ROOT = Path(r"E:\Agent\TFTF-blender")
HIER_JSON = ROOT / "tools" / "vortex" / "grindor_45_vh_hierarchy.json"
hier_data = json.loads(HIER_JSON.read_text(encoding="utf-8"))
parents = hier_data.get("parents", {})

# Build full path for each bone from root
def get_path(bname):
    chain = [bname]
    curr = bname
    while curr in parents and parents[curr] and parents[curr] != curr:
        curr = parents[curr]
        chain.append(curr)
    # chain from root down:
    # Notice: In Unity Mecanim, the path is relative to the Animator root!
    # Let's check with and without root
    return "/".join(reversed(chain))

def get_path_no_root(bname):
    chain = [bname]
    curr = bname
    while curr in parents and parents[curr] and parents[curr] != curr:
        curr = parents[curr]
        chain.append(curr)
    # omit top root
    if len(chain) > 1:
        return "/".join(reversed(chain[:-1]))
    return bname

# Unity's string hash for path in generic bindings
# Unity uses CRC32 or simple hash?
# Unity uses CRC32 on the string!
# Let's check both
def unity_hash(s):
    # Unity uses CRC32
    return zlib.crc32(s.encode('utf-8'))

# Check against clip bindings
p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle")
if not p_bundle.exists():
    p_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")

env = UnityPy.load(str(p_bundle))

# Let's check how the clip's bindings map to bones
clip_hashes = set()
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            for b in tree.get("m_ClipBindingConstant", {}).get("genericBindings", []):
                clip_hashes.add(b.get("path"))

print(f"Clip unique path hashes: {len(clip_hashes)}")

# Test combinations of prefix + bone paths
for bname in parents:
    paths_to_test = [
        bname,
        get_path(bname),
        get_path_no_root(bname),
        f"character_vehicle_model/{get_path(bname)}",
        f"character_vehicle_model/{bname}",
        f"Grindor_Cin_ROTF/{get_path(bname)}",
        f"cha_grindor_cin_rotf_01/{get_path(bname)}",
    ]
    for p in paths_to_test:
        h = unity_hash(p)
        if h in clip_hashes:
            print(f"[MATCH] Bone '{bname}' -> path '{p}' (hash {h})")

