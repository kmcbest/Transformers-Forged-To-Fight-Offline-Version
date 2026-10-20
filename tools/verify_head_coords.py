from PIL import Image
import numpy as np

nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"
opt_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_main_a.png"

nem_arr = np.array(Image.open(nem_path).convert("RGB"), dtype=np.float32)
opt_arr = np.array(Image.open(opt_path).convert("RGB"), dtype=np.float32)

H, W, _ = nem_arr.shape
yy, xx = np.mgrid[0:H, 0:W]

# Head box is in X [0, 260], Y [0, 260]
is_head_box = (xx < 260) & (yy < 260)

# In Optimus, the helmet is Blue, faceplate is white/silver, crest is blue/yellow
is_opt_blue = (opt_arr[:, :, 2] > opt_arr[:, :, 0] + 20) & (opt_arr[:, :, 2] > opt_arr[:, :, 1])
is_opt_silver = (np.abs(opt_arr[:, :, 0] - opt_arr[:, :, 1]) < 15) & (np.abs(opt_arr[:, :, 1] - opt_arr[:, :, 2]) < 15) & (opt_arr[:, :, 0] > 70)

# On the head:
# Helmet shell = is_head_box & is_opt_blue
# Faceplate = is_head_box & is_opt_silver & (xx < 140) & (yy > 130)
# Crest / Brow = is_head_box & (xx < 60) & (yy < 95)
# Eyes = is_head_box & (xx > 25) & (xx < 80) & (yy > 140) & (yy < 175) & (nem_arr[:, :, 0] > 100)

is_faceplate = is_head_box & is_opt_silver & (xx < 140) & (yy > 130) & (yy < 260)
is_crest = is_head_box & (xx < 60) & (yy < 95)
is_eyes = is_head_box & (xx > 30) & (xx < 80) & (yy > 140) & (yy < 175)
is_helmet = is_head_box & is_opt_blue & ~is_crest

print(f"Faceplate pixels: {np.sum(is_faceplate)}")
print(f"Crest pixels: {np.sum(is_crest)}")
print(f"Eyes pixels: {np.sum(is_eyes)}")
print(f"Helmet pixels: {np.sum(is_helmet)}")
