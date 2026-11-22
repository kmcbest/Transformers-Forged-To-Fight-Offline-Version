import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/brawl_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == 7575930771601290721:
        diff = np.array(obj.read().image.convert("RGBA"))
    if obj.path_id == -8652859075577142890:
        raoe = np.array(obj.read().image.convert("RGB"))

h, w = diff.shape[:2]

for obj in env.objects:
    if obj.path_id == 8927022796776742380:
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
        sampled_raoe = raoe[py, px, 2]
        
        for idx in range(270, 396):
            rgb = sampled_diff[idx]
            em = sampled_raoe[idx]
            tp = tri_pos[idx]
            tu = tri_uvs[idx]
            is_yellow = (rgb[0] > 140) and (rgb[1] > 110) and (rgb[2] < 90)
            if is_yellow or em > 30:
                print(f"Tri {idx}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tu[0]:.3f}, {tu[1]:.3f}), RGB={rgb}, RAOE.B={em}, Yellow={is_yellow}")
