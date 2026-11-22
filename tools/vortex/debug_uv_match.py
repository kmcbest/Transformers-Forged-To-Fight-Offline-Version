import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json, subprocess, UnityPy, numpy as np

with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\source_vh_polys.json", "r", encoding="utf-8") as f:
    src = json.load(f)
print("Source polys 0..5:")
for sp in src[:6]:
    print(" ", sp)

raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
vh_m = [o.read() for o in env_h.objects if o.path_id == -2766188856892899435][0]
vc = vh_m.m_VertexData.m_VertexCount
raw = bytes(vh_m.m_VertexData.m_DataSize)
s1_off = (vc * 40 + 15) & ~15
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=s1_off)
ib = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

print("\nHEAD tris 58..64:")
for ti in range(58, 65):
    print(" ", ti, [(round(float(uv[vi][0]), 4), round(float(uv[vi][1]), 4)) for vi in ib[ti]])
