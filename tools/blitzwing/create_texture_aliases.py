import sys
from pathlib import Path
import shutil

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_DIRS = [
    ROOT / "tools" / "blitzwing" / "atlased_textures",
    ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Textures",
    ROOT / "3rd-party-models" / "Blitzwing_EW" / "02_textures",
]

for td in TEX_DIRS:
    for suffix in ["Diffuse.png", "Normal.png", "Normal_unity.png", "RAOE.png", "Emission.png"]:
        src = td / f"cha_blitzwing_main_{suffix}"
        dst = td / f"cha_blitzwing_gs_00_{suffix}"
        if src.exists():
            shutil.copy2(src, dst)
        src_v = td / f"cha_blitzwing_tform_misc_{suffix}"
        dst_v1 = td / f"cha_blitzwing_gs_01_{suffix}"
        dst_v2 = td / f"cha_blitzwing_gs_02_{suffix}"
        if src_v.exists():
            shutil.copy2(src_v, dst_v1)
            shutil.copy2(src_v, dst_v2)

print("Texture aliases created successfully.")
