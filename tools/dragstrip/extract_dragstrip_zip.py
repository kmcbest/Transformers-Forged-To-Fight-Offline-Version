import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zipfile
from pathlib import Path

zip_path = Path(r"o:\agent\transformers-alliance-drag-strip.zip")
out_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\DragStrip\source")
out_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as z:
    for info in z.infolist():
        print(f"ZIP: {info.filename} ({info.file_size:,} bytes)")
    z.extractall(out_dir)

print(f"\nExtracted to {out_dir}:")
for p in sorted(out_dir.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(out_dir)} ({p.stat().st_size:,} bytes)")
