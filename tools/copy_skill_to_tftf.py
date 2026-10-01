import shutil
from pathlib import Path

src = Path(r"e:\Agent\TFTF-blender\.agents\skills\tftf_revival\SKILL.md")
dst = Path(r"e:\Agent\TFTF\.agents\skills\tftf_revival\SKILL.md")

shutil.copy2(src, dst)
print("Copied to", dst)
print("Size:", dst.stat().st_size)
