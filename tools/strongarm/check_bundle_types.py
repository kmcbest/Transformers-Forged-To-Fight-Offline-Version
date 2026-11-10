import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
from collections import Counter

moves_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
env = UnityPy.load(str(moves_path))
counts = Counter(obj.type.name for obj in env.objects)
print("Asset types in moves.assetbundle:")
for k, v in counts.items():
    print(f"  {k}: {v}")
