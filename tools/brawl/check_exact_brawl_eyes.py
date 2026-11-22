import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/brawl_gs.assetbundle')
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
        
        mask = (tri_uvs[:, 0] > 0.64) & (tri_uvs[:, 0] < 0.74) & (tri_uvs[:, 1] > 0.29) & (tri_uvs[:, 1] < 0.34)
        indices = np.where(mask)[0]
        print(f"Brawl eye UV region triangles: {len(indices)}")
        print("Indices:", list(indices))
        for idx in indices:
            tp = tri_pos[idx]
            tu = tri_uvs[idx]
            print(f"  Tri {idx}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tu[0]:.3f}, {tu[1]:.3f})")
