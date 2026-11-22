import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json, subprocess, UnityPy, numpy as np
from scipy.spatial import cKDTree

with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\prep_vh_polys.json", "r", encoding="utf-8") as f:
    prep = json.load(f)

raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
vh_m = [o.read() for o in env_h.objects if o.path_id == -2766188856892899435][0]
vc = vh_m.m_VertexData.m_VertexCount
raw = bytes(vh_m.m_VertexData.m_DataSize)
s1_off = (vc * 40 + 15) & ~15
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
ib  = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

u_c0 = pos[ib[59]].mean(axis=0)
p_c0 = np.array([prep[0]["center"][0], prep[0]["center"][2], prep[0]["center"][1]])
shift = u_c0 - p_c0

prep_pts = np.array([[p["center"][0], p["center"][2], p["center"][1]] for p in prep]) + shift
unity_pts = pos[ib].mean(axis=1)

tree = cKDTree(prep_pts)
dists, idxs = tree.query(unity_pts, k=5)

used_prep = set()
counts = {0: 0, 1: 0, 2: 0}
logo_tris = []
interior_tris = []
big_uv_diffs = []

for ti in range(len(ib)):
    u_uv = np.array(sorted(uv[ib[ti]].tolist()))
    best_pi = None
    best_score = 1e9
    for cand_pi, d in zip(idxs[ti], dists[ti]):
        pi = int(cand_pi)
        if pi in used_prep or d > 0.01:
            continue
        p_uv = np.array(sorted(prep[pi]["uvs"]))
        uvd = float(np.abs(u_uv - p_uv).max())
        score = d * 100.0 + uvd
        if score < best_score:
            best_score = score
            best_pi = pi
            best_uvd = uvd
    used_prep.add(best_pi)
    mi = prep[best_pi]["mat_idx"]
    counts[mi] += 1
    if mi == 0:
        logo_tris.append(ti)
    elif mi == 2:
        interior_tris.append(ti)
    if best_uvd > 0.01:
        big_uv_diffs.append((ti, best_pi, mi, best_uvd, uv[ib[ti]].round(3).tolist(), np.array(prep[best_pi]["uvs"]).round(3).tolist()))

print(f"Matched counts: {counts} (expected 0:4, 1:5756, 2:443)")
print(f"Tris with UV diff > 0.01: {len(big_uv_diffs)}")
for item in big_uv_diffs[:10]:
    print(" ", item)

assert counts == {0: 4, 1: 5756, 2: 443}
with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\vh_submesh_split.json", "w", encoding="utf-8") as f:
    json.dump({"logo_tris": logo_tris, "interior_tris": interior_tris}, f)
print("[✓] Saved EXACT 1-to-1 vh_submesh_split.json (4 / 5756 / 443)!")
