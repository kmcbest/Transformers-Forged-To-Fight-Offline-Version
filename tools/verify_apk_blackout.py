import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path("build/Transformers-9.2-offline-ability-refactor.apk")
print(f"Checking APK: {apk_path.resolve()} (size: {apk_path.stat().st_size} bytes)")

checks = [
    "assets/assetpack/blackout_cin_tf_odr/blackout_cin_tf.assetbundle",
    "assets/blackout_cin_tf_odr/toc.txt",
    "assets/assetpack/portraits_odr/portraits/portrait_blackout_c_tf_large.png",
    "assets/assetpack/portraits_odr/portraits/portrait_blackout_c_tf_small.jpg",
    "assets/assetpack/questboard_odr/questboard/portrait_blackout_c_tf_quest.png",
    "lib/arm64-v8a/libdothook.so",
    "assets/assetpack/characters/moves.assetbundle",
    "assets/tftf_offline_payload.bin",
]

with zipfile.ZipFile(apk_path, 'r') as zf:
    namelist = set(zf.namelist())
    for item in checks:
        if item in namelist:
            info = zf.getinfo(item)
            print(f"  [OK] Found {item} ({info.file_size} bytes)")
        else:
            print(f"  [FAIL] Missing {item}")

    # Check master toc
    if "assets/master_odr/toc.txt" in namelist:
        import json
        master_toc = json.loads(zf.read("assets/master_odr/toc.txt").decode('utf-8', errors='replace'))
        packs = master_toc.get("packs", {})
        if "blackout_cin_tf_odr" in packs:
            print(f"  [OK] Master TOC contains 'blackout_cin_tf_odr'")
        else:
            print(f"  [FAIL] Master TOC missing 'blackout_cin_tf_odr'")

    # Check portraits toc
    if "assets/portraits_odr/toc.txt" in namelist:
        import json
        ptoc = json.loads(zf.read("assets/portraits_odr/toc.txt").decode('utf-8', errors='replace'))
        files = ptoc.get("files", [])
        has_large = any("blackout" in f and "large" in f for f in files)
        has_small = any("blackout" in f and "small" in f for f in files)
        print(f"  [OK] Portraits TOC contains blackout: large={has_large}, small={has_small}")

print("\nVerification complete!")
