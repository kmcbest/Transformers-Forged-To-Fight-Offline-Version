import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == -2766188856892899435: # cha_grindor_cin_rotf_01
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        norm = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[vc*12:vc*24], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        
        print("Helicopter Mesh triangles:", len(ib))
        # Let's inspect the first 10 triangles
        for i in range(10):
            v = ib[i]
            print(f"Tri {i}: verts={v}")
            for vi in v:
                print(f"  v{vi}: pos={pos[vi]}, norm={norm[vi]}, uv={uv[vi]}")
