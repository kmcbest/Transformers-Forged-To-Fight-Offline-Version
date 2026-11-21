import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path

SRC_DIR = Path(r"E:\Agent\TFTF-blender\scratch\inspect_swoop")
DEST_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master")
DEST_DIR.mkdir(parents=True, exist_ok=True)

fbx_src = SRC_DIR / "source" / "Swoop_pbr.fbx"
shutil.copy2(fbx_src, DEST_DIR / "Swoop_pbr.fbx")

tex_dest = DEST_DIR / "textures"
tex_dest.mkdir(parents=True, exist_ok=True)
for f in (SRC_DIR / "textures").iterdir():
    shutil.copy2(f, tex_dest / f.name)

print(f"[✓] Localized Swoop source files into {DEST_DIR}")
