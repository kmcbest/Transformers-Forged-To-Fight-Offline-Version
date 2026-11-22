import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
env_head = UnityPy.load(head_path)
map_head = {o.path_id: o for o in env_head.objects}

vh_obj = map_head[-2766188856892899435]
vh_m = vh_obj.read()
vh_tt = vh_obj.read_typetree()

print("HEAD vh len(vh_m.m_IndexBuffer):", len(vh_m.m_IndexBuffer))
print("HEAD vh len(vh_tt['m_IndexBuffer']):", len(vh_tt['m_IndexBuffer']))

ib_m = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
print("HEAD vh tris around 58..65 from vh_m.m_IndexBuffer:")
for i in range(58, 66):
    print(f"  Tri {i}: {ib_m[i]}")

# Find ALL triangles using any vertex in 171..178
print("HEAD vh tris using vertices 171..178:")
for i, tri in enumerate(ib_m):
    if any(v in range(171, 179) for v in tri):
        print(f"  Tri {i}: {tri}")

# Check ALL head triangles in Robot Mesh around 6070..6110 in HEAD
rob_obj = map_head[5703189533076905359]
rob_m = rob_obj.read()
rob_ib = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
vc = rob_m.m_VertexData.m_VertexCount
raw = bytes(rob_m.m_VertexData.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
rob_diff = np.array(map_head[-527106191474585865].read().image.convert("RGBA"))
rob_raoe = np.array(map_head[-2574972184015167263].read().image.convert("RGB"))
h, w = rob_diff.shape[:2]

print("\nHEAD Robot Head ALL tris with Y > 10.2 and abs(X) < 0.35 and Z > 0.15:")
for i, tri in enumerate(rob_ib):
    tp = pos[tri].mean(axis=0)
    if tp[1] > 10.2 and abs(tp[0]) < 0.35 and tp[2] > 0.15:
        tu = uv[tri].mean(axis=0)
        px = int(np.clip(tu[0] * w, 0, w - 1))
        py = int(np.clip((1.0 - tu[1]) * h, 0, h - 1))
        rgb = rob_diff[py, px, :3]
        em = rob_raoe[py, px, 2]
        if em > 0 or (rgb[0] > 150 and rgb[1] > 150):
            print(f"  Tri {i}: Pos=({tp[0]:.3f}, {tp[1]:.3f}, {tp[2]:.3f}), UV=({tu[0]:.3f}, {tu[1]:.3f}), px=({px},{py}), RGB={rgb}, RAOE.B={em}")
