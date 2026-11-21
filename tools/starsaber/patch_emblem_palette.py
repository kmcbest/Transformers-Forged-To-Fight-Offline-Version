import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

# First, let's prepare the clean patches in cha_starsaber_main textures
TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\StarSaber\Textures")
REDECO_DIR = Path(r"E:\Agent\TFTF-blender\assets_redeco")

# We use UV region:
# U in [0.35, 0.40], V in [0.40, 0.45]
# In 2048x2048:
# X in [716..820], Y in [1126..1228] (where Y = (1-V)*2048)
# Red patch: X in [716..768], Y in [1126..1228] -> UV U=0.362, V=0.425
# Black patch: X in [768..820], Y in [1126..1228] -> UV U=0.388, V=0.425

print("Updating textures with clean emblem palette...")
diff_path = TEX_DIR / "cha_starsaber_main_Diffuse.png"
diff = Image.open(diff_path).convert("RGB")
diff_arr = np.array(diff)

# Red patch (vibrant Autobot red)
diff_arr[1126:1228, 716:768] = [215, 25, 28]
# Black patch (clean dark charcoal background)
diff_arr[1126:1228, 768:820] = [22, 22, 26]

diff_out = Image.fromarray(diff_arr)
diff_out.save(diff_path)
diff_out.save(Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\02_textures\cha_starsaber_main_Diffuse.png"))
print("  Diffuse updated.")

# RAOE:
raoe_path = TEX_DIR / "cha_starsaber_main_RAOE.png"
raoe = Image.open(raoe_path).convert("RGB")
raoe_arr = np.array(raoe)
# Red patch: Roughness=175, AO=255, Emissive=0
raoe_arr[1126:1228, 716:768] = [175, 255, 0]
# Black patch: Roughness=160, AO=255, Emissive=0
raoe_arr[1126:1228, 768:820] = [160, 255, 0]
raoe_out = Image.fromarray(raoe_arr)
raoe_out.save(raoe_path)
raoe_out.save(Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\02_textures\cha_starsaber_main_RAOE.png"))
print("  RAOE updated.")

# Normal:
norm_path = TEX_DIR / "cha_starsaber_main_Normal.png"
norm = Image.open(norm_path).convert("RGB")
norm_arr = np.array(norm)
# Nx=128, Ny=128, Metallic=0 for painted red
norm_arr[1126:1228, 716:768] = [128, 128, 0]
# Nx=128, Ny=128, Metallic=40 for dark charcoal
norm_arr[1126:1228, 768:820] = [128, 128, 40]
norm_out = Image.fromarray(norm_arr)
norm_out.save(norm_path)
norm_out.save(Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\02_textures\cha_starsaber_main_Normal.png"))
print("  Normal updated.")

print("[✓] Clean emblem palette stamped successfully!")
