from PIL import Image
from pathlib import Path

tex_dir = Path("3rd-party-models/transformers-galatic-trials-elita-one/textures")
d00 = Image.open(tex_dir / "T_VH11_00_D.png")
d01 = Image.open(tex_dir / "T_VH11_01_D.png")
print("d00 size:", d00.size, d00.mode)
print("d01 size:", d01.size, d01.mode)
