import shutil
from pathlib import Path

src = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_toxitron_main_a.png")
dst = Path(r"E:\Agent\TFTF-blender\assets_redeco\cha_toxitron_main_a.png")

shutil.copy2(src, dst)
print(f"Copied to {dst} ({dst.stat().st_size} bytes)")
