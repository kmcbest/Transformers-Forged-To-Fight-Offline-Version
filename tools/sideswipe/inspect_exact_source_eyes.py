import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

src_em_p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Emission.png")
src_diff_p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")

em = np.array(Image.open(src_em_p).convert("L")) # 4096 x 4096
diff = np.array(Image.open(src_diff_p).convert("RGB"))

# Downsample to 2048 x 2048 using box or area resize
em_2048 = np.array(Image.fromarray(em).resize((2048, 2048), Image.Resampling.BOX))
diff_2048 = np.array(Image.fromarray(diff).resize((2048, 2048), Image.Resampling.LANCZOS))

# Find non-zero pixels in em_2048
y_nz, x_nz = np.where(em_2048 > 20)
print(f"Non-zero emission pixels in 2048 space: {len(y_nz)}")
for y, x in zip(y_nz, x_nz):
    print(f"  (y={y}, x={x}): Em={em_2048[y, x]}, Diffuse RGB={diff_2048[y, x]}")
