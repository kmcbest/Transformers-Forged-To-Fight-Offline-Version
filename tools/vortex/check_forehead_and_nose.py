import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
env = UnityPy.load(head_path)
obj_map = {o.path_id: o for o in env.objects}

rob_diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_diff.png").convert("RGB"))
rob_raoe = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_raoe.png").convert("RGB"))
h, w = rob_diff.shape[:2]

rob_m = obj_map[5703189533076905359].read()
vd = rob_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
ib = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

tri_pos = pos[ib].mean(axis=1)
tri_uvs = uv[ib].mean(axis=1)
px = np.clip((tri_uvs[:, 0] * w).astype(int), 0, w - 1)
py = np.clip(((1.0 - tri_uvs[:, 1]) * h).astype(int), 0, h - 1)

print("Tris hitting X=[1075..1110], Y=[1750..1800]:")
for i in range(len(ib)):
    if 1075 <= px[i] <= 1110 and 1750 <= py[i] <= 1800:
        print(f"  Tri {i}: Pos={tri_pos[i].round(3)}, px=({px[i]},{py[i]}), RGB={rob_diff[py[i], px[i]]}, RAOE.B={rob_raoe[py[i], px[i], 2]}")

print("Tris hitting X=[1410..1470], Y=[1840..1940]:")
for i in range(len(ib)):
    if 1410 <= px[i] <= 1470 and 1840 <= py[i] <= 1940:
        print(f"  Tri {i}: Pos={tri_pos[i].round(3)}, px=({px[i]},{py[i]}), RGB={rob_diff[py[i], px[i]]}, RAOE.B={rob_raoe[py[i], px[i], 2]}")
