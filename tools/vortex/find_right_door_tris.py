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
        
        # Right door: X in [0.7..1.3], Y in [2.6..3.5], Z in [0.15..1.3]
        right_door = []
        for i, tri in enumerate(ib):
            if i in (59, 60, 61, 62): continue
            tp = pos[tri].mean(axis=0)
            tu = uv[tri].mean(axis=0)
            if 0.7 < tp[0] < 1.3 and 2.6 < tp[1] < 3.5 and 0.18 < tp[2] < 1.3:
                right_door.append((i, tp, tu))
        print("Right door triangles count:", len(right_door))
        for r in right_door:
            print(f"  Tri {r[0]}: Pos={r[1]}, UV={r[2]}")
