import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image

img = Image.open(r"C:\Users\Xiangli496\.gemini\antigravity\brain\73f5038e-a9de-4967-848d-46abd8c1bd80\.user_uploaded\media_1795224120851_8a3eaa2a.jpg")
w, h = img.size
print("Original size:", w, h)

# Crop around the sword hilt and red 90 deg arrow
crop = img.crop((int(0.3 * w), int(0.4 * h), int(0.9 * w), int(0.9 * h)))
crop.save(r"E:\Agent\TFTF-blender\scratch\sword_arrow_zoom.png")
print("Saved scratch\\sword_arrow_zoom.png")
