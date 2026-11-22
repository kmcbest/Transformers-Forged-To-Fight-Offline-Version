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

# 1. Check head_vh_raoe.png channels
vh_raoe = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_vh_raoe.png"))
print("=== head_vh_raoe.png stats ===")
for ch, name in enumerate(["R", "G", "B"]):
    print(f"  {name}: min={vh_raoe[:,:,ch].min()}, max={vh_raoe[:,:,ch].max()}, mean={vh_raoe[:,:,ch].mean():.2f}, nonzero={(vh_raoe[:,:,ch]>0).sum()}")

# 2. Check head_robot_raoe.png stats by region
rob_raoe = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_raoe.png"))
rob_diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_diff.png").convert("RGB"))
print("\n=== head_robot_raoe.png stats ===")
print(f"  Overall B: min={rob_raoe[:,:,2].min()}, max={rob_raoe[:,:,2].max()}, nonzero={(rob_raoe[:,:,2]>0).sum()}")

# Find all triangles on chest (Y in [7.0..9.8], Z > 0.3) and check their UVs & diffuse colors
rob_m = obj_map[5703189533076905359].read()
vd = rob_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
ib = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

h, w = rob_diff.shape[:2]
tri_pos = pos[ib].mean(axis=1)
tri_uvs = uv[ib].mean(axis=1)
px = np.clip((tri_uvs[:, 0] * w).astype(int), 0, w - 1)
py = np.clip(((1.0 - tri_uvs[:, 1]) * h).astype(int), 0, h - 1)

# Find triangles mapped to the top-right Decepticon emblem tile (px > 1536, py < 512)
emblem_tris = []
for i in range(len(ib)):
    if px[i] >= 1536 and py[i] < 512:
        emblem_tris.append(i)
print(f"\n=== Robot triangles mapped to top-right Decepticon logo tile (px>=1536, py<512): {len(emblem_tris)} ===")
if emblem_tris:
    epos = tri_pos[emblem_tris]
    print(f"  Pos X=[{epos[:,0].min():.2f}..{epos[:,0].max():.2f}], Y=[{epos[:,1].min():.2f}..{epos[:,1].max():.2f}], Z=[{epos[:,2].min():.2f}..{epos[:,2].max():.2f}]")
    print(f"  Sample RAOE.B on emblem tris: min={rob_raoe[py[emblem_tris], px[emblem_tris], 2].min()}, max={rob_raoe[py[emblem_tris], px[emblem_tris], 2].max()}")

# Find chest diagonal vent / grille triangles:
# Front chest in Unity: Y in [7.8..9.4], |X| in [0.25..1.6], Z > 0.35
# Look for purple/blue pixels in chest diffuse tile (px < 1024, py >= 1024)
print("\n=== Robot Chest Triangles with Blue/Purple Grille Diffuse (px<1024, py>=1024, B > R+15) ===")
chest_grille_tris = []
for i in range(len(ib)):
    tp = tri_pos[i]
    if 7.5 < tp[1] < 9.5 and 0.25 < abs(tp[0]) < 1.8 and tp[2] > 0.2:
        if px[i] < 1024 and py[i] >= 1024:
            rgb = rob_diff[py[i], px[i]]
            if int(rgb[2]) > int(rgb[0]) + 10:
                chest_grille_tris.append(i)
                print(f"  Tri {i}: Pos=({tp[0]:.2f}, {tp[1]:.2f}, {tp[2]:.2f}), UV=({tri_uvs[i,0]:.3f}, {tri_uvs[i,1]:.3f}), px=({px[i]},{py[i]}), RGB={rgb}, RAOE.B={rob_raoe[py[i], px[i], 2]}")
print(f"Total chest grille tris: {len(chest_grille_tris)}")

# Also find ALL glowing triangles in the ENTIRE robot mesh (RAOE.B > 10)
glow_tris = np.where(rob_raoe[py, px, 2] > 10)[0]
print(f"\n=== ALL currently glowing tris in HEAD robot (RAOE.B > 10): {len(glow_tris)} ===")
# Group by 256x256 tile
from collections import Counter
tile_counts = Counter((int(px[i]//256), int(py[i]//256)) for i in glow_tris)
for tile, cnt in tile_counts.most_common():
    sample_i = [i for i in glow_tris if (int(px[i]//256), int(py[i]//256)) == tile][0]
    print(f"  Tile ({tile[0]}, {tile[1]}) [X={tile[0]*256}..{(tile[0]+1)*256}, Y={tile[1]*256}..{(tile[1]+1)*256}]: {cnt} tris, sample Pos={tri_pos[sample_i].round(2)}, sample RAOE.B={rob_raoe[py[sample_i], px[sample_i], 2]}")
