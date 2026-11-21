import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

src_diff = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")
arr = np.array(src_diff)
w, h = src_diff.size
x = int(0.414 * w)
y = int((1.0 - 0.615) * h)

patch = arr[y-100:y+100, x-100:x+100]
# Find pixels where R > G+40 and R > B+40
mask = (patch[:, :, 0].astype(int) > patch[:, :, 1].astype(int) + 40) & (patch[:, :, 0].astype(int) > patch[:, :, 2].astype(int) + 40)
pys, pxs = np.where(mask)
print(f"In patch: {len(pxs)} reddish pixels")
if len(pxs) > 0:
    sample_colors = patch[pys[:5], pxs[:5]]
    print("Sample red colors:", sample_colors)
    print("Max R:", patch[pys, pxs, 0].max(), "Min R:", patch[pys, pxs, 0].min())
    print("Mean G:", patch[pys, pxs, 1].mean(), "Mean B:", patch[pys, pxs, 2].mean())

# Now search whole image with this broader condition
full_mask = (arr[:, :, 0].astype(int) > arr[:, :, 1].astype(int) + 40) & (arr[:, :, 0].astype(int) > arr[:, :, 2].astype(int) + 40)
fys, fxs = np.where(full_mask)
print(f"In whole image: {len(fxs)} reddish pixels")

from scipy.ndimage import label
lbl, num = label(full_mask)
for i in range(1, num + 1):
    cys, cxs = np.where(lbl == i)
    if len(cxs) > 500:
        print(f"Big Cluster {i}: {len(cxs)} pixels, X=[{cxs.min()}, {cxs.max()}], Y=[{cys.min()}, {cys.max()}] (UV: U=[{cxs.min()/w:.3f}, {cxs.max()/w:.3f}], V=[{1-cys.max()/h:.3f}, {1-cys.min()/h:.3f}])")
