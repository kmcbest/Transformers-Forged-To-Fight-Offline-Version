import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

wire = np.array(Image.open('e:/Agent/TFTF-blender/tools/vortex/uv_wireframe_helicopter.png'))
# green wire was drawn with G > 200 and R == 0
# let's find connected components of empty areas where no polygon was drawn!
# In draw_helicopter_uv_wireframe.py, overlay was fill=(0, 255, 0, 60).
# But let's check exact polygon coverage on a binary mask:
from PIL import ImageDraw
import UnityPy

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == -2766188856892899435:
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16)
        
        mask = Image.new("1", (1024, 1024), 0)
        draw = ImageDraw.Draw(mask)
        emblem_tris = set([59, 60, 61, 62])
        for t_i in range(len(ib) // 3):
            if t_i in emblem_tris:
                continue
            tri = ib[t_i*3 : t_i*3+3]
            pts = [(int(np.clip(uv[vi, 0] * 1024, 0, 1023)), int(np.clip((1.0 - uv[vi, 1]) * 1024, 0, 1023))) for vi in tri]
            draw.polygon(pts, fill=1)
            
        mask_np = np.array(mask)
        uncovered = (mask_np == 0)
        print("Total uncovered pixels:", uncovered.sum(), f"({uncovered.sum() / mask_np.size * 100:.2f}%)")
        
        # Check squares of size 64x64, 48x48, 32x32
        for sz in [128, 96, 64, 48, 32]:
            found = []
            for y in range(0, 1024 - sz, 8):
                for x in range(0, 1024 - sz, 8):
                    if np.all(uncovered[y:y+sz, x:x+sz]):
                        found.append((x, y))
            print(f"Size {sz}x{sz} completely empty blocks: {len(found)}")
            if found:
                print(f"  First 3 empty blocks of size {sz}: {found[:3]}")
