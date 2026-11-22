import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image
from scipy.ndimage import label

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
env = UnityPy.load(head_path)
obj_map = {o.path_id: o for o in env.objects}

rob_diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_diff.png").convert("RGB"))
rob_raoe = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_raoe.png").convert("RGB"))
h, w = rob_diff.shape[:2]

print("=== All RAOE.B > 0 connected components in head_robot_raoe.png ===")
b_mask = rob_raoe[:, :, 2] > 10
lbl, num = label(b_mask)
for i in range(1, num + 1):
    ys, xs = np.where(lbl == i)
    if len(ys) > 10:
        print(f"  Comp {i}: pixels={len(ys)}, X=[{xs.min()}..{xs.max()}], Y=[{ys.min()}..{ys.max()}], RAOE.B mean={rob_raoe[ys, xs, 2].mean():.1f}, max={rob_raoe[ys, xs, 2].max()}")

# Inspect chest grille pixels in bottom-left chest tile (X in [0..1024], Y in [1024..2048])
# Check exact RGB values in the blue honeycomb region of orig_rb_vortex_chest_mat.jpg
# Wait: in head_robot_diff.png (2048x2048), bottom-left is chest: X=[0..1024], Y=[1024..2048]
# Save a crop of the chest grille region: X=[50..400], Y=[1450..1800]
chest_crop = Image.fromarray(rob_diff[1450:1800, 50:400])
chest_crop.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\chest_grille_crop.png")
print("\nSaved chest_grille_crop.png (X=[50..400], Y=[1450..1800])")

# Save a crop of the head visor & vertical strip region: X=[1300..1500], Y=[1650..1950]
head_crop = Image.fromarray(rob_diff[1650:1950, 1300:1500])
head_crop.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_face_crop.png")
head_raoe_crop = Image.fromarray(rob_raoe[1650:1950, 1300:1500])
head_raoe_crop.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_face_raoe_crop.png")
print("Saved head_face_crop.png & head_face_raoe_crop.png")

# Inspect triangles around chest emblem and chest diagonal vents
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

print("\n=== Triangles in chest grille UV region (px in [60..360], py in [1500..1720]) ===")
cnt = 0
for i in range(len(ib)):
    if 60 <= px[i] <= 360 and 1500 <= py[i] <= 1720:
        tp = tri_pos[i]
        rgb = rob_diff[py[i], px[i]]
        cnt += 1
        if cnt <= 25:
            print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), px=({px[i]},{py[i]}), RGB={rgb}")
print(f"Total tris mapped to px=[60..360], py=[1500..1720]: {cnt}")

# Also check which chest triangles map to the center-top square [1024..1536, 512..1024]!
print("\n=== Triangles mapped to center-top purple square (px in [1024..1536], py in [512..1024]) ===")
sq_tris = [i for i in range(len(ib)) if 1024 <= px[i] < 1536 and 512 <= py[i] < 1024]
print(f"Total tris: {len(sq_tris)}")
if sq_tris:
    spos = tri_pos[sq_tris]
    print(f"  Pos X=[{spos[:,0].min():.2f}..{spos[:,0].max():.2f}], Y=[{spos[:,1].min():.2f}..{spos[:,1].max():.2f}], Z=[{spos[:,2].min():.2f}..{spos[:,2].max():.2f}]")
