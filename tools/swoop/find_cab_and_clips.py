import sys
import os
import glob
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ramjet_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
renv = UnityPy.load(ramjet_path)
robjs = {o.path_id: o for o in renv.objects}
print("=== Ramjet original AOCs ===")
for aoc_pid in (6432204470035570307, -6340484879223379266):
    aoc = robjs[aoc_pid].read_typetree()
    print(f"AOC {aoc_pid} ({aoc.get('m_Name')}):")
    for idx, p in enumerate(aoc["m_Clips"]):
        if idx in (5, 12, 16, 58):
            over = p["m_OverrideClip"]["m_PathID"]
            fid = p["m_OverrideClip"]["m_FileID"]
            print(f"  [{idx}] orig={p['m_OriginalClip']} over=({fid}, {over}) name={robjs[over].read().m_Name if (fid==0 and over in robjs) else 'EXT'}")

# Scan assetpack for CAB-a742a3fff84aa604ba32daca2b1ea500
ap_dir = r"E:\Agent\TFTF\extracted_apk\assets\assetpack"
for root, _, files in os.walk(ap_dir):
    for f in files:
        if f.endswith(".assetbundle"):
            p = os.path.join(root, f)
            try:
                with open(p, "rb") as fp:
                    head = fp.read(4096)
                e = UnityPy.load(p)
                for fn in e.file.files.keys():
                    if "a742a3fff84aa604ba32daca2b1ea500" in fn or "47012f9f52e0ee1cac4dfad2d29a972d" in fn:
                        print(f"\nMATCH CAB in {p}: {fn}")
                        for o in e.objects:
                            if o.path_id in (7645321843667068633, -7632205551962568777, 5214496857524066160):
                                tt = o.read_typetree()
                                print(f"  OBJ {o.path_id}: {tt.get('m_Name')} stop={tt.get('m_MuscleClip',{}).get('m_StopTime')} bindings={len(tt.get('m_ClipBindingConstant',{}).get('genericBindings',[]))}")
            except Exception:
                pass
