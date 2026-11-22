import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

# Load original DecepticonLogo.png (128x128 RGBA)
logo_raw = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\DecepticonLogo.png").convert("RGBA")
# Resize logo to 400x400 with Lanczos
logo_resized = logo_raw.resize((400, 400), Image.Resampling.LANCZOS)
logo_np = np.array(logo_resized)

# Background color matching helicopter golden door: RGB = [182, 164, 74]
diff_512 = np.zeros((512, 512, 4), dtype=np.uint8)
diff_512[:, :, 0] = 182
diff_512[:, :, 1] = 164
diff_512[:, :, 2] = 74
diff_512[:, :, 3] = 255

# RAOE: R=160 (roughness), G=255 (AO), B=0 (emissive)
raoe_512 = np.zeros((512, 512, 3), dtype=np.uint8)
raoe_512[:, :, 0] = 160
raoe_512[:, :, 1] = 255
raoe_512[:, :, 2] = 0

# Center offset: (512 - 400) // 2 = 56
y_off = 56
x_off = 56

logo_alpha = logo_np[:, :, 3] / 255.0 # (400, 400) float
# Blend logo in diffuse
# Make the logo bright purple: [130, 20, 210]
logo_purple = np.zeros((400, 400, 3), dtype=np.float32)
logo_purple[:, :, 0] = 130
logo_purple[:, :, 1] = 20
logo_purple[:, :, 2] = 210

bg_patch = diff_512[y_off:y_off+400, x_off:x_off+400, :3].astype(np.float32)
alpha_3d = logo_alpha[:, :, np.newaxis]
blended = bg_patch * (1.0 - alpha_3d) + logo_purple * alpha_3d
diff_512[y_off:y_off+400, x_off:x_off+400, :3] = np.clip(blended, 0, 255).astype(np.uint8)

# In RAOE, set emissive channel B = 220 * alpha
emissive_patch = (logo_alpha * 220.0).astype(np.uint8)
raoe_512[y_off:y_off+400, x_off:x_off+400, 2] = emissive_patch

diff_out = Image.fromarray(diff_512)
raoe_out = Image.fromarray(raoe_512)

diff_out.save(r"e:\Agent\TFTF-blender\tools\vortex\emblem_diff_512.png")
raoe_out.save(r"e:\Agent\TFTF-blender\tools\vortex\emblem_raoe_512.png")
print("Saved emblem_diff_512.png and emblem_raoe_512.png successfully!")
