import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

ab_path = r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"
env = UnityPy.load(ab_path)

for obj in env.objects:
    if obj.type.name == "Mesh" and obj.read().m_Name == "cha_grindor_cin_rotf_01":
        m = obj.read()
        vd = m.m_VertexData
        vc = vd.m_VertexCount
        raw = vd.m_DataSize
        pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
        uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)
        
        for vi in range(171, 179):
            print(f"Vertex {vi}: Pos={pos[vi]}, UV={uv[vi]}")
