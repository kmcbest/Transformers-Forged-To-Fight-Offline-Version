import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
for f in SRC.iterdir():
    if "blastoff" in f.name.lower() or "head" in f.name.lower():
        print(f"File: {f.name}")
        try:
            im = Image.open(f)
            print(f"   size={im.size}, mode={im.mode}")
        except Exception:
            pass
