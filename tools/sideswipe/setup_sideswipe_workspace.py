import sys
import os
import shutil
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

base_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe")
src_dir = base_dir / "01_source"
tex_dir = base_dir / "02_textures"
fbx_dir = base_dir / "03_fbx_exports"
tools_dir = Path(r"E:\Agent\TFTF-blender\tools\sideswipe")
unity_tex_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Sideswipe\Textures")

for d in [src_dir, tex_dir, fbx_dir, tools_dir, unity_tex_dir]:
    d.mkdir(parents=True, exist_ok=True)
    print(f"Created/Verified directory: {d}")

# Copy extracted scratch files to 01_source
scratch_dir = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\scratch")
scratch_tex = scratch_dir / "textures"

for fbx in ["Sideswipe.fbx", "Sideswipe_Car.fbx"]:
    s = scratch_dir / fbx
    if s.exists():
        shutil.copy2(s, src_dir / fbx)
        print(f"Copied {fbx} to {src_dir}")

src_tex = src_dir / "textures"
src_tex.mkdir(parents=True, exist_ok=True)

if scratch_tex.exists():
    for f in scratch_tex.iterdir():
        if f.is_file():
            shutil.copy2(f, src_tex / f.name)
    print(f"Copied textures to {src_tex}")
