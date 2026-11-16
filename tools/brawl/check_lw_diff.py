import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
brawl_path = Path("assets_redeco/brawl_gs.assetbundle")

env_d = UnityPy.load(str(donor_path))
env_b = UnityPy.load(str(brawl_path))

f_d = [f for f in env_d.files.values() if hasattr(f, 'objects')][0] if any(hasattr(f, 'objects') for f in env_d.files.values()) else list(list(env_d.files.values())[0].files.values())[0]
f_b = [f for f in env_b.files.values() if hasattr(f, 'objects')][0] if any(hasattr(f, 'objects') for f in env_b.files.values()) else list(list(env_b.files.values())[0].files.values())[0]

ab_d = next(o for o in f_d.objects.values() if o.type.name == "AssetBundle").read()
ab_b = next(o for o in f_b.objects.values() if o.type.name == "AssetBundle").read()

# Donor lw slice
lw_d = [v for k, v in ab_d.m_Container if "_lw" in k][0]
preload_d = ab_d.m_PreloadTable
lw_d_objs = preload_d[lw_d.preloadIndex : lw_d.preloadIndex + lw_d.preloadSize]

# Brawl lw slice
lw_b = [v for k, v in ab_b.m_Container if "_lw" in k][0]
preload_b = ab_b.m_PreloadTable
lw_b_objs = preload_b[lw_b.preloadIndex : lw_b.preloadIndex + lw_b.preloadSize]

set_d = set((p.m_FileID, p.m_PathID) for p in lw_d_objs)
set_b = set((p.m_FileID, p.m_PathID) for p in lw_b_objs)

print(f"Donor lw preload count: {len(lw_d_objs)}")
print(f"Brawl lw preload count: {len(lw_b_objs)}")

diff_d_b = set_d - set_b
print(f"\nIn Donor but NOT in Brawl ({len(diff_d_b)}):")
for fid, pid in diff_d_b:
    obj = f_d.objects.get(pid)
    tname = obj.type.name if obj else "Unknown"
    print(f"  fid={fid}, pid={pid}, type={tname}")

diff_b_d = set_b - set_d
print(f"\nIn Brawl but NOT in Donor ({len(diff_b_d)}):")
for fid, pid in diff_b_d:
    obj = f_b.objects.get(pid)
    tname = obj.type.name if obj else "Unknown"
    print(f"  fid={fid}, pid={pid}, type={tname}")
