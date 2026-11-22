import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image

env = UnityPy.load('assets_redeco/brawl_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == 7575930771601290721:
        diff_img = obj.read().image.convert("RGBA")
    if obj.path_id == -8652859075577142890:
        raoe_img = obj.read().image.convert("RGB")

diff = np.array(diff_img)
raoe = np.array(raoe_img)
h, w = diff.shape[:2]

for obj in env.objects:
    if obj.path_id == 8927022796776742380: # cha_brawl_gs_00
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        
        tri_uvs = uv[ib].mean(axis=1)
        tri_pos = pos[ib].mean(axis=1)
        
        px = np.clip((tri_uvs[:, 0] * w).astype(int), 0, w - 1)
        py = np.clip(((1.0 - tri_uvs[:, 1]) * h).astype(int), 0, h - 1)
        sampled_diff = diff[py, px, :3]
        sampled_em = raoe[py, px, 2]
        
        print("Brawl pos bounds:", pos.min(axis=0), pos.max(axis=0))
        # Head is top Y
        # Let's inspect glowing triangles on the head (Y > 10.0, or check upper range)
        head_mask = (tri_pos[:, 1] > 9.5)
        print(f"Total head triangles (Y > 9.5): {head_mask.sum()}")
        
        glowing_head = np.where(head_mask & (sampled_em > 50))[0]
        print(f"Glowing head triangles (RAOE.B > 50): {len(glowing_head)}")
        for idx in glowing_head:
            tp = tri_pos[idx]
            tu = tri_uvs[idx]
            rgb = sampled_diff[idx]
            em = sampled_em[idx]
            print(f"  Brawl Head Glow Tri {idx}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tu[0]:.3f}, {tu[1]:.3f}), RGB={rgb}, RAOE.B={em}")
