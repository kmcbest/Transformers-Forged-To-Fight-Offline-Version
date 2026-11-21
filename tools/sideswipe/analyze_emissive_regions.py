import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

DIFF_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png")
RAOE_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_RAOE.png")
BODY_DIFF_ORIG = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")
BODY_LIGHTS_ORIG = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Lights.png")
BODY_EM_ORIG = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Emission.png")

diff = np.array(Image.open(DIFF_PATH))
raoe = np.array(Image.open(RAOE_PATH))
em_mask = raoe[:, :, 2]

print("=== Emissive Mask Analysis ===")
print("Emissive pixels > 50:", np.sum(em_mask > 50))
print("Emissive max:", em_mask.max())

# Find all regions with em_mask > 100
ys, xs = np.where(em_mask > 100)
print(f"Y range: [{ys.min()} .. {ys.max()}], X range: [{xs.min()} .. {xs.max()}]")

# Sample colors at emissive pixels
em_diff = diff[ys, xs]
print(f"Mean Diffuse RGB at emissive pixels: R={em_diff[:,0].mean():.1f}, G={em_diff[:,1].mean():.1f}, B={em_diff[:,2].mean():.1f}")

# Check original Body_Lights and Body_Emission
if BODY_LIGHTS_ORIG.exists():
    bl = np.array(Image.open(BODY_LIGHTS_ORIG))
    print(f"Original Body_Lights shape: {bl.shape}, max: {bl.max()}")
    if bl.max() > 0:
        ys_bl, xs_bl = np.where(bl.mean(axis=2) > 20) if len(bl.shape) == 3 else np.where(bl > 20)
        print(f"  Body_Lights active pixels: Y=[{ys_bl.min()}..{ys_bl.max()}], X=[{xs_bl.min()}..{xs_bl.max()}]")

if BODY_EM_ORIG.exists():
    be = np.array(Image.open(BODY_EM_ORIG))
    print(f"Original Body_Emission shape: {be.shape}, max: {be.max()}")
    if be.max() > 0:
        ys_be, xs_be = np.where(be.mean(axis=2) > 20) if len(be.shape) == 3 else np.where(be > 20)
        print(f"  Body_Emission active pixels: Y=[{ys_be.min()}..{ys_be.max()}], X=[{xs_be.min()}..{xs_be.max()}]")
