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

# 1. Check Comp 1 (Chest Emblem tile X=[1536..2048], Y=[0..512])
emblem_diff_crop = rob_diff[0:512, 1536:2048]
emblem_raoe_crop = rob_raoe[0:512, 1536:2048]
print("=== Top-Right Chest Emblem Tile Stats ===")
b = emblem_diff_crop[:, :, 2].astype(int)
g = emblem_diff_crop[:, :, 1].astype(int)
r = emblem_diff_crop[:, :, 0].astype(int)
purp_face = (b > g + 40) & (b > 130)
print(f"  Purple logo face pixels: {purp_face.sum()}, RAOE.B mean on face={emblem_raoe_crop[purp_face, 2].mean():.1f}")
non_purp_lit = (~purp_face) & (emblem_raoe_crop[:, :, 2] > 10)
print(f"  NON-purple (black outline/crevices!) pixels currently lit in RAOE.B: {non_purp_lit.sum()} (RAOE.B mean={emblem_raoe_crop[non_purp_lit, 2].mean():.1f})")

# 2. Check ALL triangles mapped to head visor box [1355..1465, 1665..1722]
print("\n=== ALL triangles hitting Head Visor box px=[1355..1465], py=[1665..1722] ===")
for i in range(len(ib)):
    if 1355 <= px[i] <= 1465 and 1665 <= py[i] <= 1722:
        tp = tri_pos[i]
        print(f"  Tri {i}: Pos=({tp[0]:.3f}, {tp[1]:.3f}, {tp[2]:.3f}), px=({px[i]},{py[i]}), RGB={rob_diff[py[i], px[i]]}, RAOE.B={rob_raoe[py[i], px[i], 2]}")

# 3. Check ALL triangles on head with Y > 10.0 and Z > 0.15 that hit any RAOE.B > 10
print("\n=== ALL head triangles (Y>10.0) hitting ANY RAOE.B > 10 ===")
for i in range(len(ib)):
    if tri_pos[i, 1] > 10.0 and rob_raoe[py[i], px[i], 2] > 10:
        tp = tri_pos[i]
        print(f"  Tri {i}: Pos=({tp[0]:.3f}, {tp[1]:.3f}, {tp[2]:.3f}), px=({px[i]},{py[i]}), RAOE.B={rob_raoe[py[i], px[i], 2]}")

# 4. Check wpns_NM and tform_misc_NM
for pid, name in [(4939845825144636112, "wpns_NM"), (-7687136803950198041, "tform_misc_NM")]:
    im = np.array(obj_map[pid].read().image.convert("RGB"))
    print(f"\nTexture {name} ({pid}): shape={im.shape}, mean RGB={im.mean(axis=(0,1)).round(1)}")
