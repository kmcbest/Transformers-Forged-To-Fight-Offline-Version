from PIL import Image
import numpy as np

nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"
nem_arr = np.array(Image.open(nem_path).convert("RGB"), dtype=np.float32)

H, W, _ = nem_arr.shape
yy, xx = np.mgrid[0:H, 0:W]

is_nem_red = (nem_arr[:, :, 0] > 160) & (nem_arr[:, :, 1] < 40) & (nem_arr[:, :, 2] < 40)
print(f"Nemesis pure red pixels: {np.sum(is_nem_red)}")

is_windshield = is_nem_red & (xx < 400) & (yy > 400) & (yy < 700)
yw, xw = np.where(is_windshield)
print(f"Windshield bounding box: X [{min(xw)}, {max(xw)}], Y [{min(yw)}, {max(yw)}], Count: {len(yw)}")
