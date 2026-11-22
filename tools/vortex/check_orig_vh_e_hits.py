import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess, UnityPy, numpy as np
from PIL import Image

orig_vh_e = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\orig_vh.jpg").convert("RGB"))
raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
vh_m = [o.read() for o in env_h.objects if o.path_id == -2766188856892899435][0]
vc = vh_m.m_VertexData.m_VertexCount
raw = bytes(vh_m.m_VertexData.m_DataSize)
s1_off = (vc * 40 + 15) & ~15
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
ib  = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

tri_pos = pos[ib].mean(axis=1)
tri_uv  = uv[ib].mean(axis=1)
h, w = orig_vh_e.shape[:2]
px = np.clip((tri_uv[:, 0] % 1.0) * w, 0, w - 1).astype(int)
py = np.clip((1.0 - (tri_uv[:, 1] % 1.0)) * h, 0, h - 1).astype(int)
em_val = orig_vh_e[py, px].max(axis=1)

hits = np.where(em_val > 35)[0]
print(f"Tris hitting orig_vh.jpg emissive (>35): {len(hits)}")
for ti in hits[:25]:
    print(f"  Tri {ti}: Pos={tri_pos[ti].round(2)}, px=({px[ti]},{py[ti]}), em_rgb={orig_vh_e[py[ti], px[ti]]}")
