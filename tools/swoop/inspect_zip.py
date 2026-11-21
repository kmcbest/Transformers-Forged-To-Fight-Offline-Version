import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
from pathlib import Path

ZIP_PATH = Path(r"o:\agent\transformers-alliance-swoop.zip")
print(f"Inspecting zip: {ZIP_PATH}")

if ZIP_PATH.exists():
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for info in z.infolist():
            print(f"  {info.filename} ({info.file_size / 1024:.1f} KB)")
else:
    print("Zip file does not exist at path!")
