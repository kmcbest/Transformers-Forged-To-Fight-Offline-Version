import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

BW = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
MEGA = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")

bw_env = UnityPy.load(str(BW))
mg_env = UnityPy.load(str(MEGA))

bw_sf = next(f for f in bw_env.file.files.values() if hasattr(f, "objects"))
mg_sf = next(f for f in mg_env.file.files.values() if hasattr(f, "objects"))

print(f"MEGA objects: {len(mg_sf.objects)}, BLITZWING objects: {len(bw_sf.objects)}")
print("Extra/Missing PIDs in BLITZWING:")
print("  Added:", set(bw_sf.objects.keys()) - set(mg_sf.objects.keys()))
print("  Removed:", set(mg_sf.objects.keys()) - set(bw_sf.objects.keys()))

# Try reading EVERY object in BLITZWING via read_typetree() and verify no read error or truncated data!
errs = 0
for pid, o in bw_sf.objects.items():
    try:
        tt = o.read_typetree()
    except Exception as ex:
        print(f"  [READ ERR] {pid} ({o.type.name}): {ex}")
        errs += 1
print(f"Total read_typetree errors in BLITZWING: {errs}")

# Check m_Container and m_PreloadTable in BLITZWING vs MEGA
bw_ab = next(o.read_typetree() for o in bw_env.objects if o.type.name == "AssetBundle")
mg_ab = next(o.read_typetree() for o in mg_env.objects if o.type.name == "AssetBundle")
print("MEGA PreloadTable len:", len(mg_ab["m_PreloadTable"]), "BLITZWING PreloadTable len:", len(bw_ab["m_PreloadTable"]))
print("BLITZWING Container:", bw_ab["m_Container"])
# Check any preload entries in BLITZWING whose FileID is NOT in 1..len(externals) or FileID==0 missing
ext_count = len(bw_sf.externals)
for p in bw_ab["m_PreloadTable"]:
    fid, pid = p["m_FileID"], p["m_PathID"]
    if fid < 0 or fid > ext_count:
        print(f"  [BAD PRELOAD FID] {p}")
    elif fid == 0 and pid not in bw_sf.objects:
        print(f"  [BAD PRELOAD LOCAL] {p}")

# Check Showcase & Combat Root Prefabs' m_PreloadTable sizes in m_Container!
# IMPORTANT: Check preloadIndex and preloadSize in m_Container!!
print("MEGA Container:", mg_ab["m_Container"])
