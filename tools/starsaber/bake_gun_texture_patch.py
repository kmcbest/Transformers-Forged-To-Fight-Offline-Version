import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
from pathlib import Path
import numpy as np

print("=== [StarSaber] Baking Gun Textures into cha_starsaber_wpns atlas ===")

SRC_TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\textures")
DST_TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\02_textures")

gun_d = Image.open(SRC_TEX_DIR / "Tx_StarSaberGun_D.png").convert("RGB").resize((256, 512), Image.Resampling.LANCZOS)
gun_n = Image.open(SRC_TEX_DIR / "Tx_StarSaberGun_N.png").convert("RGB").resize((256, 512), Image.Resampling.LANCZOS)
gun_s = Image.open(SRC_TEX_DIR / "Tx_StarSaberGun_S.png").convert("RGB").resize((256, 512), Image.Resampling.LANCZOS)

# 1. Diffuse: paste into right half of cha_starsaber_wpns_Diffuse.png
diff = Image.open(DST_TEX_DIR / "cha_starsaber_wpns_Diffuse.png").convert("RGB")
diff.paste(gun_d, (256, 0))
diff.save(DST_TEX_DIR / "cha_starsaber_wpns_Diffuse.png")
print("[✓] Patched cha_starsaber_wpns_Diffuse.png")

# 2. Normal: R = Norm.R, G = Norm.G, B = 0 (dielectric metal armor), A = 255
norm_orig = Image.open(DST_TEX_DIR / "cha_starsaber_wpns_Normal.png").convert("RGBA")
gun_n_arr = np.array(gun_n)
gun_norm_rgba = np.zeros((512, 256, 4), dtype=np.uint8)
gun_norm_rgba[:, :, 0] = gun_n_arr[:, :, 0]  # Norm X
gun_norm_rgba[:, :, 1] = gun_n_arr[:, :, 1]  # Norm Y
gun_norm_rgba[:, :, 2] = 0                   # Dielectric armor (NM.B = 0)
gun_norm_rgba[:, :, 3] = 255
norm_orig.paste(Image.fromarray(gun_norm_rgba, "RGBA"), (256, 0))
norm_orig.save(DST_TEX_DIR / "cha_starsaber_wpns_Normal.png")
print("[✓] Patched cha_starsaber_wpns_Normal.png")

# 3. RAOE: R = Roughness (S.G), A = AO (S.B), O = 255, E = 0
raoe_orig = Image.open(DST_TEX_DIR / "cha_starsaber_wpns_RAOE.png").convert("RGBA")
gun_s_arr = np.array(gun_s)
gun_raoe_rgba = np.zeros((512, 256, 4), dtype=np.uint8)
gun_raoe_rgba[:, :, 0] = gun_s_arr[:, :, 1]  # R = Roughness (from S.G)
gun_raoe_rgba[:, :, 1] = gun_s_arr[:, :, 2]  # A = Ambient Occlusion (from S.B)
gun_raoe_rgba[:, :, 2] = 0                   # O = Occlusion / Cavity
gun_raoe_rgba[:, :, 3] = 0                   # E = Emission (0 for gun)
raoe_orig.paste(Image.fromarray(gun_raoe_rgba, "RGBA"), (256, 0))
raoe_orig.save(DST_TEX_DIR / "cha_starsaber_wpns_RAOE.png")
print("[✓] Patched cha_starsaber_wpns_RAOE.png")
