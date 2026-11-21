import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from PIL import Image, ImageDraw
import numpy as np

FBX_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

ab = bpy.data.objects.get("Symbol_AB.001")
uv_layer = ab.data.uv_layers.active

img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

for poly in ab.data.polygons:
    pts = []
    for l in poly.loop_indices:
        u, v = uv_layer.data[l].uv
        x = int(u * 1024)
        y = int((1.0 - v) * 1024)
        pts.append((x, y))
    col = (255, 0, 0, 200) if poly.material_index == 0 else (0, 0, 0, 255)
    draw.polygon(pts, fill=col, outline=(255, 255, 255, 128))

img.save(r"E:\Agent\TFTF-blender\scratch\symbol_uv_layout.png")
print("Saved E:\Agent\TFTF-blender\scratch\symbol_uv_layout.png")
