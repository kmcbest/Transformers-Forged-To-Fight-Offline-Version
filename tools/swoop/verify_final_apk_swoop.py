import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zipfile
import json
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\out\Transformers-9.2-offline-blender2.apk")
assert apk_path.is_file(), f"APK missing: {apk_path}"

with zipfile.ZipFile(apk_path, "r") as zf:
    namelist = set(zf.namelist())
    
    # 1. Check bundle in APK
    bundle_name = "assets/assetpack/swoop_gs_deluxe2008_odr/swoop_gs_deluxe2008.assetbundle"
    assert bundle_name in namelist, f"Missing {bundle_name} in APK!"
    print(f"[PASS] Found {bundle_name} ({zf.getinfo(bundle_name).file_size} bytes)")

    # 2. Check toc.txt for swoop
    toc_name = "assets/swoop_gs_deluxe2008_odr/toc.txt"
    assert toc_name in namelist, f"Missing {toc_name} in APK!"
    toc_data = json.loads(zf.read(toc_name).decode("utf-8"))
    paths = toc_data["bundles"]["swoop_gs_deluxe2008"]["paths"]
    print(f"[PASS] Found {toc_name}, paths: {paths}")

    # 3. Check portraits in APK
    for p in [
        "assets/assetpack/portraits_odr/portraits/portrait_swoop_small.jpg",
        "assets/assetpack/portraits_odr/portraits/portrait_swoop_large.png",
        "assets/assetpack/portraits_odr/portraits/portrait_swoop_gs_deluxe2008_small.jpg",
        "assets/assetpack/portraits_odr/portraits/portrait_swoop_gs_deluxe2008_large.png",
        "assets/assetpack/dialogue_odr/dialogue/swoop.png",
        "assets/assetpack/questboard_odr/questboard/portrait_swoop_quest.png",
    ]:
        assert p in namelist, f"Missing portrait file {p} in APK!"
        print(f"[PASS] Found portrait {p} ({zf.getinfo(p).file_size} bytes)")

    # 4. Check portraits toc.txt
    ptoc_name = "assets/portraits_odr/toc.txt"
    ptoc_data = json.loads(zf.read(ptoc_name).decode("utf-8"))
    pfiles = set(ptoc_data.get("files", []))
    assert "portraits/portrait_swoop_small.jpg" in pfiles, "Missing portrait_swoop_small.jpg in ptoc!"
    assert "portraits/portrait_swoop_large.png" in pfiles, "Missing portrait_swoop_large.png in ptoc!"
    print(f"[PASS] Verified portraits_odr/toc.txt contains swoop portraits!")

print("\n🎉 ALL APK SWOOP CHECKS VERIFIED 100%!")
