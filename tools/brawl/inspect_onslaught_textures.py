import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

im = Image.open(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Onslaught\cha_onslaught_main_a.png")
print("Onslaught Robot Main Diffuse:", im.size, im.mode)

im_vh = Image.open(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Onslaught\cha_onslaught_vh_a.png")
print("Onslaught Vehicle Diffuse:", im_vh.size, im_vh.mode)
