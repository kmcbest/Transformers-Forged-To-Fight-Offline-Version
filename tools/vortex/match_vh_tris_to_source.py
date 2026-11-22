import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
import numpy as np
import json
from collections import defaultdict

with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\source_vh_polys.json", "r", encoding="utf-8") as f:
    src_polys = json.load(f)

raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
obj_map = {o.path_id: o for o in env_h.objects}

vh_m = obj_map[-2766188856892899435].read()
vd = vh_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
s1_off = (vc * 40 + 15) & ~15
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
ib  = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

# Build quantized UV-triplet lookup for source polys
def norm_tri_uv(uv_list):
    return tuple(sorted((round(float(u), 3), round(float(v), 3)) for u, v in uv_list))

src_by_uv = defaultdict(list)
for sp in src_polys:
    src_by_uv[norm_tri_uv(sp["uvs"])].append(sp)

mat_counts = defaultdict(int)
interior_tris = []
logo_tris = []
unmatched = 0

for ti in range(len(ib)):
    key = norm_tri_uv(uv[ib[ti]])
    cands = src_by_uv.get(key)
    if not cands:
        unmatched += 1
        continue
    # If multiple mirror polys share identical UVs, pick the mat_idx (if unanimous, guaranteed exact!)
    mats = {c["mat_idx"] for c in cands}
    if len(mats) > 1:
        # check if TR_Test_Mat_INST collides with VH_VortexBase_MAT on UV?
        print(f"  Collision on Tri {ti}: mats={mats}")
    mi = cands[0]["mat_idx"]
    mat_counts[mi] += 1
    if mi == 0:
        logo_tris.append(ti)
    elif mi == 2:
        interior_tris.append(ti)

print(f"\nMatched {len(ib) - unmatched}/{len(ib)} tris! Unmatched: {unmatched}")
print("Matched material counts:", dict(mat_counts))
print(f"Logo tris ({len(logo_tris)}): {logo_tris}")
print(f"Interior TR_Test_Mat_INST tris ({len(interior_tris)}): first 10={interior_tris[:10]}, last 10={interior_tris[-10:]}")

with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\vh_submesh_split.json", "w", encoding="utf-8") as f:
    json.dump({"logo_tris": logo_tris, "interior_tris": interior_tris}, f)
print("Saved vh_submesh_split.json")
