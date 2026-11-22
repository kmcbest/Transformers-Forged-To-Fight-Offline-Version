import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == 5703189533076905359:
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        ib = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
        
        diff = None
        raoe = None
        for o in env.objects:
            if o.path_id == -527106191474585865:
                diff = np.array(o.read().image.convert("RGBA"))
            if o.path_id == -2574972184015167263:
                raoe = np.array(o.read().image.convert("RGB"))
                
        h, w = diff.shape[:2]
        
        for idx in range(6070, 6115):
            tp = pos[ib[idx]].mean(axis=0)
            tu = uv[ib[idx]].mean(axis=0)
            px = int(np.clip(tu[0] * w, 0, w - 1))
            py = int(np.clip((1.0 - tu[1]) * h, 0, h - 1))
            rgb = diff[py, px, :3]
            em = raoe[py, px, 2]
            print(f"Tri {idx}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tu[0]:.3f}, {tu[1]:.3f}), RGB={rgb}, RAOE.B={em}")
