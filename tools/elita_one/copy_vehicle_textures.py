import shutil
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_SRC = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures"
TEX_DST = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "Vehicle"
TEX_DST.mkdir(parents=True, exist_ok=True)

files = [
    "T_VH11_00_D.png", "T_VH11_00_N.png", "T_VH11_00_R.png", "T_VH11_00_O.png", "mat_vh0_glow.tga.png",
    "T_VH11_01_D.png", "T_VH11_01_N.png", "T_VH11_01_R.png", "T_VH11_01_O.png", "mat_vh1_glow.tga.png"
]

for f in files:
    src = TEX_SRC / f
    dst = TEX_DST / f
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copied {f} -> {dst}")
    else:
        print(f"Warning: {f} not found at {src}")

print("Texture copy complete!")
