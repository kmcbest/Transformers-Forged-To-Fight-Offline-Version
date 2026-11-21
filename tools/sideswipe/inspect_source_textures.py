import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures")
diff_img = Image.open(SRC / "Body_Diffuse.png")
em_img = Image.open(SRC / "Body_Emission.png")

diff_arr = np.array(diff_img)
em_arr = np.array(em_img)

# Left eye: X in [1480, 1505], Y in [3494, 3512]
# Right eye: X in [1648, 1672], Y in [3494, 3512]
for name, (x0, x1) in [("Left Eye", (1480, 1505)), ("Right Eye", (1648, 1672))]:
    box_diff = diff_arr[3494:3512, x0:x1]
    box_em = em_arr[3494:3512, x0:x1]
    active = box_em > 20
    print(f"\n{name}: {np.sum(active)} emissive pixels")
    r_mean = box_diff[active, 0].mean() if np.any(active) else 0
    g_mean = box_diff[active, 1].mean() if np.any(active) else 0
    b_mean = box_diff[active, 2].mean() if np.any(active) else 0
    print(f"  Diffuse RGB: R={r_mean:.1f}, G={g_mean:.1f}, B={b_mean:.1f}")

# What about the rest of Body_Emission? Are there any other pixels in Body_Emission?
other_ys, other_xs = np.where((em_arr > 20) & ((diff_arr.mean(axis=2) < 0) | True))
print(f"\nTotal non-zero in Body_Emission: {len(other_ys)}")
# Check if any other Y outside 3490..3515 has emission in Body_Emission
out_ys = [y for y in other_ys if y < 3490 or y > 3515]
print(f"Pixels outside eyes in Body_Emission: {len(out_ys)}")
