import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path
import datetime

so_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\lib\arm64-v8a\libdothook.so")
if so_path.exists():
    print(f"libdothook.so: size={so_path.stat().st_size} mtime={datetime.datetime.fromtimestamp(so_path.stat().st_mtime)}")
else:
    print("libdothook.so NOT FOUND")
