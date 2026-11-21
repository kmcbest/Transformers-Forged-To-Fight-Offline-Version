import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
print(f"=== Verifying final APK: {apk_path} ===")
assert apk_path.is_file(), f"APK not found: {apk_path}"

with zipfile.ZipFile(apk_path, "r") as zf:
    names = set(zf.namelist())
    
    # Check assetbundle
    ab_entries = [n for n in names if "sideswipe_cin_rotf.assetbundle" in n]
    print(f"Found sideswipe assetbundle entries: {ab_entries}")
    assert len(ab_entries) > 0, "sideswipe_cin_rotf.assetbundle missing from APK!"
    
    # Check portraits
    portrait_entries = [n for n in names if "sideswipe" in n.lower() and "portrait" in n.lower()]
    print(f"Found sideswipe portrait entries ({len(portrait_entries)}):")
    for p in sorted(portrait_entries):
        print(f"  {p}")
    assert len(portrait_entries) > 0, "sideswipe portraits missing from APK!"
    
    # Check native hook & payload
    assert "lib/arm64-v8a/libdothook.so" in names, "libdothook.so missing!"
    assert "assets/tftf_offline_payload.bin" in names, "offline payload missing!"
    print(f"[✓] APK Verification Passed Cleanly! Total files in APK: {len(names)}, Size: {apk_path.stat().st_size / (1024*1024):.2f} MB")
