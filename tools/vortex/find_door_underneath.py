import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == -2766188856892899435:
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        
        # Emblem center is around |X| ≈ 1.0, Y ≈ 3.0, Z ≈ 0.8
        for i in range(len(ib)):
            if i in (59, 60, 61, 62):
                continue
            tp = pos[ib[i]].mean(axis=0)
            tu = uv[ib[i]].mean(axis=0)
            if abs(tp[0] - 1.0) < 0.25 and abs(tp[1] - 3.0) < 0.35 and abs(tp[2] - 0.8) < 0.35:
                print(f"Fuselage door Tri {i}: Pos={tp}, UV={tu}")
