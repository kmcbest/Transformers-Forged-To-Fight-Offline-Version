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

# 1. Check ALL triangles mapped to chest_grille_crop (X=[50..400], Y=[1450..1800]) with B > R + 20 (purple/blue honeycomb)
print("=== Checking honeycomb chest grille UV region ===")
honey_tris = []
for i in range(len(ib)):
    x, y = px[i], py[i]
    if 60 <= x <= 350 and 1490 <= y <= 1700:
        r, g, b = int(rob_diff[y, x, 0]), int(rob_diff[y, x, 1]), int(rob_diff[y, x, 2])
        if b > r + 15 and b > g + 10:
            honey_tris.append((i, tri_pos[i], (x, y), (r, g, b)))
print(f"Honeycomb blue/purple grille tris: {len(honey_tris)}")
for i, tp, pxy, rgb in honey_tris:
    print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), px={pxy}, RGB={rgb}")

# Check ALL pixels in chest_grille_crop with b > r + 15 and b > g + 10
sub = rob_diff[1490:1700, 60:350].astype(int)
mask_honey = (sub[:, :, 2] > sub[:, :, 0] + 15) & (sub[:, :, 2] > sub[:, :, 1] + 10)
print(f"Total honeycomb blue/purple pixels in [60..350, 1490..1700]: {mask_honey.sum()}")

# Check if ANY non-chest triangles map into [60..350, 1490..1700] where mask_honey is true
print("Checking if any non-chest triangles hit honeycomb pixels:")
for i in range(len(ib)):
    x, y = px[i], py[i]
    if 60 <= x < 350 and 1490 <= y < 1700:
        if mask_honey[y - 1490, x - 60]:
            tp = tri_pos[i]
            if tp[1] < 8.5 or tp[1] > 10.0:
                print(f"  NON-CHEST? Tri {i}: Pos={tp.round(2)}, px=({x},{y})")

# 2. Check ALL triangles near Chest Emblem (X in [-0.4..0.4], Y in [8.4..9.6], Z > 0.7)
print("\n=== Checking Chest Center Emblem tris (|X|<0.4, Y in [8.4..9.7], Z>0.7) ===")
for i in range(len(ib)):
    tp = tri_pos[i]
    if abs(tp[0]) < 0.4 and 8.4 < tp[1] < 9.7 and tp[2] > 0.7:
        x, y = px[i], py[i]
        em = rob_raoe[y, x, 2]
        if em > 0 or x >= 1536:
            print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), px=({x},{y}), RGB={rob_diff[y,x]}, RAOE.B={em}")

# 3. Check ALL triangles in Head Visor / Face area (|X| < 0.4, Y in [10.0..11.1], Z > 0.1)
print("\n=== Checking ALL Face tris with RAOE.B > 0 or yellow (|X|<0.4, Y in [10.0..11.1], Z>0.1) ===")
for i in range(len(ib)):
    tp = tri_pos[i]
    if abs(tp[0]) < 0.4 and 10.0 < tp[1] < 11.1 and tp[2] > 0.1:
        x, y = px[i], py[i]
        r, g, b = rob_diff[y, x]
        em = rob_raoe[y, x, 2]
        if em > 0 or (int(r) > 150 and int(g) > 140 and int(b) < 130):
            print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), px=({x},{y}), RGB={[r,g,b]}, RAOE.B={em}")

# 4. Check where the SWORD BLADE is!
print("\n=== Checking Sword Blade / Comp 2 tris (px in [1024..1535], py in [512..1023]) ===")
# Wait: earlier Comp 2 Pos was Y=[0.96..4.61], X=[-2.88..2.82] - let's print a few sample tris
cnt = 0
for i in range(len(ib)):
    x, y = px[i], py[i]
    if 1024 <= x < 1536 and 512 <= y < 1024:
        tp = tri_pos[i]
        cnt += 1
        if cnt <= 10:
            print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), px=({x},{y}), RAOE.B={rob_raoe[y,x,2]}")
print(f"Total Comp 2 tris: {cnt}")
