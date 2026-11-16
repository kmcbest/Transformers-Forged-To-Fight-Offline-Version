import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
BRAWL = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"

env_d = UnityPy.load(str(DONOR))
env_b = UnityPy.load(str(BRAWL))

def get_preload_slice(env, cname_substr):
    ab = next(o for o in env.objects if o.type.name == "AssetBundle").read_typetree()
    for name, info in ab.get("m_Container", []):
        if cname_substr in name:
            idx = info["preloadIndex"]
            sz = info["preloadSize"]
            return ab["m_PreloadTable"][idx:idx+sz]
    return []

donor_lw = [(p["m_FileID"], p["m_PathID"]) for p in get_preload_slice(env_d, "_lw.prefab")]
brawl_lw = [(p["m_FileID"], p["m_PathID"]) for p in get_preload_slice(env_b, "_lw.prefab")]

print(f"Donor LW preload count: {len(donor_lw)}")
print(f"Brawl LW preload count: {len(brawl_lw)}")

donor_set = set(donor_lw)
brawl_set = set(brawl_lw)

only_donor = donor_set - brawl_set
only_brawl = brawl_set - donor_set

print(f"In Donor LW only ({len(only_donor)}):")
obj_map_d = {o.path_id: o for o in env_d.objects}
for fid, pid in list(only_donor)[:20]:
    o = obj_map_d.get(pid)
    print(f"  fid={fid}, pid={pid}, type={o.type.name if o else 'None'}")

print(f"\nIn Brawl LW only ({len(only_brawl)}):")
obj_map_b = {o.path_id: o for o in env_b.objects}
for fid, pid in list(only_brawl)[:20]:
    o = obj_map_b.get(pid)
    print(f"  fid={fid}, pid={pid}, type={o.type.name if o else 'None'}")
