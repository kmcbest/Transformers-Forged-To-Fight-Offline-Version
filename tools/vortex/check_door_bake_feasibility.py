import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image, ImageDraw

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
env = UnityPy.load(head_path)
obj_map = {o.path_id: o for o in env.objects}

# 1. Inspect Vortex Helicopter door UVs & overlap
vh_m = obj_map[-2766188856892899435].read()
vd = vh_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
ib = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

tri_pos = pos[ib].mean(axis=1)
tri_uvs = uv[ib].mean(axis=1)

# Emblem quads (tris 59,60 right; 61,62 left)
print("=== Emblem Quad Bounds ===")
for side, tris in [("Right", [59, 60]), ("Left", [61, 62])]:
    pts = pos[ib[tris]].reshape(-1, 3)
    print(f"  {side}: X=[{pts[:,0].min():.3f}..{pts[:,0].max():.3f}], Y=[{pts[:,1].min():.3f}..{pts[:,1].max():.3f}], Z=[{pts[:,2].min():.3f}..{pts[:,2].max():.3f}]")

# Find fuselage triangles behind/near Right & Left Emblem Quads
# Plane project distance to Right Quad
def find_door_tris(side_sign):
    # Right quad: v173 (TL), v171 (TR), v172 (BL), v174 (BR)
    # Center approx (side_sign*1.0, 3.05, 0.72)
    matched = []
    for i in range(len(ib)):
        if i in (59, 60, 61, 62):
            continue
        p = tri_pos[i]
        if side_sign * p[0] > 0.55 and side_sign * p[0] < 1.45 and 2.4 < p[1] < 3.7 and 0.0 < p[2] < 1.5:
            matched.append(i)
    return matched

r_tris = find_door_tris(+1)
l_tris = find_door_tris(-1)
print(f"\nRight door region tris ({len(r_tris)}): {r_tris}")
print(f"Left door region tris ({len(l_tris)}): {l_tris}")

# Print UV bounds in 1024x1024 pixels for right and left door tris
for name, tris in [("Right", r_tris), ("Left", l_tris)]:
    u_vals = uv[ib[tris]][:, :, 0].flatten() * 1024
    v_vals = (1.0 - uv[ib[tris]][:, :, 1].flatten()) * 1024
    print(f"  {name} door pixel bbox: X=[{u_vals.min():.1f}..{u_vals.max():.1f}], Y=[{v_vals.min():.1f}..{v_vals.max():.1f}]")

# Check overlap: do ANY other triangles outside r_tris / l_tris map into the same pixels?
mask_r = Image.new("1", (1024, 1024), 0)
dr = ImageDraw.Draw(mask_r)
for ti in r_tris:
    pts = [(float(uv[vi, 0]*1024), float((1.0 - uv[vi, 1])*1024)) for vi in ib[ti]]
    dr.polygon(pts, fill=1)

mask_l = Image.new("1", (1024, 1024), 0)
dl = ImageDraw.Draw(mask_l)
for ti in l_tris:
    pts = [(float(uv[vi, 0]*1024), float((1.0 - uv[vi, 1])*1024)) for vi in ib[ti]]
    dl.polygon(pts, fill=1)

mask_other = Image.new("1", (1024, 1024), 0)
do = ImageDraw.Draw(mask_other)
rl_set = set(r_tris) | set(l_tris) | {59, 60, 61, 62}
for ti in range(len(ib)):
    if ti in rl_set:
        continue
    pts = [(float(uv[vi, 0]*1024), float((1.0 - uv[vi, 1])*1024)) for vi in ib[ti]]
    do.polygon(pts, fill=1)

mr = np.array(mask_r)
ml = np.array(mask_l)
mo = np.array(mask_other)
print(f"\nRight door pixels: {mr.sum()}, overlap with other tris: {(mr & mo).sum()}")
print(f"Left door pixels: {ml.sum()}, overlap with other tris: {(ml & mo).sum()}")
print(f"Right/Left overlap with each other: {(mr & ml).sum()}")
