import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path

source_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber")
for root, dirs, files in os.walk(source_dir):
    for f in files:
        if f.endswith(('.fbx', '.obj', '.blend', '.png')):
            full = os.path.join(root, f)
            print(f"{os.path.relpath(full, source_dir)} ({os.path.getsize(full)} bytes)")
