import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env_b = UnityPy.load(str(BRAWL_BUNDLE))
print("Files in brawl_gs.assetbundle:")
for k in env_b.file.files.keys():
    print(" ", k)
