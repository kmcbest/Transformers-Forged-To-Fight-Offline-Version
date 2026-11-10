import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender.apk")
print(f"Inspecting {apk_path} ({apk_path.stat().st_size / (1024*1024):.2f} MB)...")

with zipfile.ZipFile(apk_path, 'r') as zf:
    names = zf.namelist()
    strongarm_files = [n for n in names if "strongarm" in n.lower()]
    print(f"\nFound {len(strongarm_files)} Strongarm files in APK:")
    for f in sorted(strongarm_files):
        info = zf.getinfo(f)
        print(f"  {f} ({info.file_size / 1024:.1f} KB)")
        
    packs_txt = None
    if "assets/packs.txt" in names:
        packs_txt = zf.read("assets/packs.txt").decode("utf-8", errors="replace")
        has_sa = "strongarm_gs" in packs_txt
        print(f"\nassets/packs.txt contains 'strongarm_gs': {has_sa}")
        if has_sa:
            for line in packs_txt.splitlines():
                if "strongarm" in line.lower():
                    print(f"  Line: {line}")
