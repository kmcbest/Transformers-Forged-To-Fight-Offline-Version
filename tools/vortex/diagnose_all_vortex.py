import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image
import zipfile
import io
import os

os.makedirs(r"e:\Agent\TFTF-blender\tools\vortex\diag", exist_ok=True)

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
curr_path = r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"

env_head = UnityPy.load(head_path)
map_head = {o.path_id: o for o in env_head.objects}

# Save clean HEAD textures for visual inspection
for pid, fname in [
    (-527106191474585865, "head_robot_diff.png"),
    (-2574972184015167263, "head_robot_raoe.png"),
    (-7643335609835079515, "head_vh_diff.png"),
    (3025951477767776163, "head_vh_raoe.png"),
]:
    img = map_head[pid].read().image
    img.save(rf"e:\Agent\TFTF-blender\tools\vortex\diag\{fname}")
    print(f"Saved {fname}: size={img.size}, mode={img.mode}")

# Check original FOC zip emissive textures for Vortex
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    for n in ["textures/rb_vortex_head_mat.jpg", "textures/rb_vortex_chest_mat.jpg", "textures/head_e.jpg", "textures/chest_e.jpg", "textures/vh_vortexbase_mat.jpg"]:
        if n in z.namelist():
            im = Image.open(io.BytesIO(z.read(n)))
            out_n = os.path.basename(n)
            im.save(rf"e:\Agent\TFTF-blender\tools\vortex\diag\orig_{out_n}")
            print(f"Extracted {n} -> orig_{out_n} ({im.size})")

# Check ALL triangles on Vortex Robot Head (Y > 9.8) in HEAD bundle
rob_m = map_head[5703189533076905359].read()
vd = rob_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
ib = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

rob_diff = np.array(map_head[-527106191474585865].read().image.convert("RGBA"))
rob_raoe = np.array(map_head[-2574972184015167263].read().image.convert("RGB"))
h, w = rob_diff.shape[:2]

tri_pos = pos[ib].mean(axis=1)
tri_uvs = uv[ib].mean(axis=1)
px = np.clip((tri_uvs[:, 0] * w).astype(int), 0, w - 1)
py = np.clip(((1.0 - tri_uvs[:, 1]) * h).astype(int), 0, h - 1)
s_diff = rob_diff[py, px, :3]
s_em = rob_raoe[py, px, 2]

print("\n=== Vortex Robot Head Glowing Triangles (Y > 9.8 and RAOE.B > 10) ===")
for i in np.where((tri_pos[:, 1] > 9.8) & (s_em > 10))[0]:
    print(f"  Tri {i}: Pos=({tri_pos[i,0]:.2f}, {tri_pos[i,1]:.2f}, {tri_pos[i,2]:.2f}), UV=({tri_uvs[i,0]:.3f}, {tri_uvs[i,1]:.3f}), px=({px[i]},{py[i]}), RGB={s_diff[i]}, RAOE.B={s_em[i]}")

# Also check current bundle's cha_grindor_cin_rotf_01 vs HEAD's cha_grindor_cin_rotf_01
env_curr = UnityPy.load(curr_path)
map_curr = {o.path_id: o for o in env_curr.objects}
vh_head = map_head[-2766188856892899435].read()
vh_curr = map_curr[-2766188856892899435].read()
vh_curr_tt = map_curr[-2766188856892899435].read_typetree()

print("\n=== Current Vortex Helicopter Mesh Check ===")
print("m_SubMeshes:", vh_curr_tt["m_SubMeshes"])
ib_curr = np.frombuffer(bytes(vh_curr.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
print("Last 6 tris in curr m_IndexBuffer:")
vc_vh = vh_curr.m_VertexData.m_VertexCount
raw_vh = bytes(vh_curr.m_VertexData.m_DataSize)
pos_vh = np.ndarray((vc_vh, 3), dtype=np.float32, buffer=raw_vh, strides=(40, 4), offset=0)
uv_vh = np.ndarray((vc_vh, 2), dtype=np.float32, buffer=raw_vh, strides=(8, 4), offset=vc_vh*40)
for idx in range(len(ib_curr)-6, len(ib_curr)):
    tri = ib_curr[idx]
    print(f"  Tri {idx}: verts={tri}, pos_mean={pos_vh[tri].mean(axis=0)}, uvs={uv_vh[tri].tolist()}")
