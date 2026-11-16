import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
assert apk_path.is_file(), f"Missing APK: {apk_path}"

with zipfile.ZipFile(apk_path, "r") as zf:
    brawl_entries = [zi for zi in zf.infolist() if "brawl" in zi.filename.lower()]
    print(f"APK size: {apk_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"Brawl entries in APK ({len(brawl_entries)}):")
    for zi in sorted(brawl_entries, key=lambda x: x.filename):
        print(f"  {zi.filename:70s} size={zi.file_size:10d} compress_type={zi.compress_type}")
    assert any("brawl_gs.assetbundle" in zi.filename and zi.file_size > 40_000_000 for zi in brawl_entries), "Missing brawl_gs.assetbundle in APK!"
    assert any("brawl_gs_odr/toc.txt" in zi.filename for zi in brawl_entries), "Missing brawl_gs_odr/toc.txt in APK!"
    print("[PASS] APK Brawl ODR & Bundle integrity verified!")
