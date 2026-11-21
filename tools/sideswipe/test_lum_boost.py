import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

src_diff_p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Diffuse.png")
diff = np.array(Image.open(src_diff_p).convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS), dtype=np.float32)

lum = diff.mean(axis=2)
sat = (diff.max(axis=2) - diff.min(axis=2)) / np.maximum(diff.max(axis=2), 1.0)

is_silver = (lum >= 40.0) & (sat < 0.22)
is_dark = lum < 40.0

print(f"Original Silver Armor: mean lum = {lum[is_silver].mean():.1f}, min={lum[is_silver].min():.1f}, max={lum[is_silver].max():.1f}")
print(f"Original Dark Joints: mean lum = {lum[is_dark].mean():.1f}")

# Test boost curve:
# We want armor to look bright silver (170..235) while preserving shading nuances
# Linear remap of armor luminance: (lum - 40) / (max - 40) -> map from [40..130] to [160..235]
boost_factor = np.where(is_silver, np.clip(2.05 + (lum - 40.0) / 100.0 * 0.4, 1.8, 2.6), 1.0)[..., None]
diff_boosted = np.clip(diff * boost_factor, 0, 245)
lum_boosted = diff_boosted.mean(axis=2)

print(f"Boosted Silver Armor: mean lum = {lum_boosted[is_silver].mean():.1f}, min={lum_boosted[is_silver].min():.1f}, max={lum_boosted[is_silver].max():.1f}")
print(f"Boosted Dark Joints: mean lum = {lum_boosted[is_dark].mean():.1f}")
