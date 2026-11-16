import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

im = Image.open(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Onslaught\cha_onslaught_main_a.png")
# Check the 4 quadrants: Top-Left (0..1024, 0..1024), Top-Right (1024..2048, 0..1024), Bottom-Left, Bottom-Right
w, h = im.size
print(f"Size: {w}x{h}")
# Check if quadrants have distinct content
q_tl = im.crop((0, 0, w//2, h//2))
q_tr = im.crop((w//2, 0, w, h//2))
q_bl = im.crop((0, h//2, w//2, h))
q_br = im.crop((w//2, h//2, w, h))

print("Quadrants colors/stddev:")
for name, q in [("Top-Left", q_tl), ("Top-Right", q_tr), ("Bottom-Left", q_bl), ("Bottom-Right", q_br)]:
    ext = q.getextrema()
    print(f"  {name}: extrema={ext}")
