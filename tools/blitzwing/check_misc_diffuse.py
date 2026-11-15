import sys
from PIL import Image
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

misc_diff_path = r"E:\Agent\TFTF-blender\tools\blitzwing\atlased_textures\cha_blitzwing_tform_misc_Diffuse.png"
img = Image.open(misc_diff_path)
print(f"cha_blitzwing_tform_misc_Diffuse: size={img.size}, mode={img.mode}")
arr = np.array(img)
print(f"R mean={arr[:,:,0].mean():.1f}, min={arr[:,:,0].min()}, max={arr[:,:,0].max()}")
print(f"G mean={arr[:,:,1].mean():.1f}, min={arr[:,:,1].min()}, max={arr[:,:,1].max()}")
print(f"B mean={arr[:,:,2].mean():.1f}, min={arr[:,:,2].min()}, max={arr[:,:,2].max()}")

# Let's check the quadrants:
# Quadrant 0 (top-left 0..2048, 0..2048), Quadrant 1 (top-right 2048..4096, 0..2048)
# Quadrant 2 (bottom-left 0..2048, 2048..4096), Quadrant 3 (bottom-right 2048..4096, 2048..4096)
w, h = img.size
q_w, q_h = w // 2, h // 2
quads = [
    ("TL (0,0)", arr[0:q_h, 0:q_w]),
    ("TR (1,0)", arr[0:q_h, q_w:w]),
    ("BL (0,1)", arr[q_h:h, 0:q_w]),
    ("BR (1,1)", arr[q_h:h, q_w:w]),
]
for name, q in quads:
    print(f"  {name}: mean RGB=({q[:,:,0].mean():.1f}, {q[:,:,1].mean():.1f}, {q[:,:,2].mean():.1f}) max={q[:,:,:3].max()}")
