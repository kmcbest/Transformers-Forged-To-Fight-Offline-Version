import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import io
import zipfile
from pathlib import Path
import UnityPy

apk_path = Path(r"E:\Agent\TFTF-blender\build\out\Transformers-9.2-offline-blender2.apk")
assert apk_path.is_file(), f"APK not found: {apk_path}"

with zipfile.ZipFile(apk_path, "r") as z:
    names = set(z.namelist())
    
    checks = [
        "assets/assetpack/blastoff_gs_odr/blastoff_gs.assetbundle",
        "assets/blastoff_gs_odr/toc.txt",
        "assets/assetpack/portraits_odr/portraits/portrait_blastoff_gs_large.png",
        "assets/assetpack/portraits_odr/portraits/portrait_blastoff_gs_small.jpg",
        "assets/assetpack/questboard_odr/questboard/portrait_blastoff_gs_quest.png",
        "assets/assetpack/dialogue_odr/dialogue/blastoff_gs.png",
        "lib/arm64-v8a/libdothook.so",
        "assets/tftf_offline_payload.bin",
    ]
    
    print("=== APK File Inspection ===")
    all_ok = True
    for c in checks:
        if c in names:
            info = z.getinfo(c)
            print(f"  [✓] Found: {c} ({info.file_size} bytes)")
        else:
            print(f"  [✗] MISSING: {c}")
            all_ok = False
            
    # Verify libdothook.so content
    dh_bytes = z.read("lib/arm64-v8a/libdothook.so")
    if b"blastoff_gs" in dh_bytes:
        print("  [✓] libdothook.so contains 'blastoff_gs' binary string")
    else:
        print("  [✗] libdothook.so MISSING 'blastoff_gs' string")
        all_ok = False

    # Verify blastoff_gs.assetbundle inside APK for CAB isolation
    bundle_bytes = z.read("assets/assetpack/blastoff_gs_odr/blastoff_gs.assetbundle")
    env = UnityPy.load(io.BytesIO(bundle_bytes))
    cab_keys = list(env.file.files.keys())
    print(f"  CAB keys in APK bundle: {cab_keys}")
    if any("CAB-7b0f00007b0f00007b0f00007b0f0001" in k for k in cab_keys) and not any("3d6c9759" in k for k in cab_keys):
        print("  [✓] blastoff_gs.assetbundle inside APK has 100% isolated CAB: CAB-7b0f00007b0f00007b0f00007b0f0001")
    else:
        print("  [✗] blastoff_gs.assetbundle inside APK has OLD or CONFLICTING CAB!")
        all_ok = False

if all_ok:
    print("\n🎉 ALL APK CHECKS PASSED PERFECTLY!")
else:
    print("\n❌ SOME APK CHECKS FAILED!")
