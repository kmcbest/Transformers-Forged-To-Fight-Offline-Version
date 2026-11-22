import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image, ImageDraw

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == -2766188856892899435:
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16)
        
        diff = Image.open('e:/Agent/TFTF-blender/tools/vortex/vh_vortexbase_mat.png').convert("RGBA")
        overlay = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # draw wireframe of all triangles except the 4 emblem triangles (tris 59, 60, 61, 62)
        emblem_tris = set([59, 60, 61, 62])
        for t_i in range(len(ib) // 3):
            if t_i in emblem_tris:
                continue
            tri = ib[t_i*3 : t_i*3+3]
            pts = [(int(np.clip(uv[vi, 0] * 1024, 0, 1023)), int(np.clip((1.0 - uv[vi, 1]) * 1024, 0, 1023))) for vi in tri]
            draw.polygon(pts, fill=(0, 255, 0, 60), outline=(0, 255, 0, 150))
            
        combined = Image.alpha_composite(diff, overlay)
        combined.save('e:/Agent/TFTF-blender/tools/vortex/uv_wireframe_helicopter.png')
        print("Saved uv_wireframe_helicopter.png")
