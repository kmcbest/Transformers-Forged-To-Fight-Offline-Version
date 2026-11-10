import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from pathlib import Path
import re

def check_yaml_mesh(path, label):
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    vc = int(re.search(r"m_VertexCount:\s*(\d+)", txt).group(1))
    hex_v = re.search(r"_typelessdata:\s*([0-9a-fA-F]+)", txt).group(1)
    hex_i = re.search(r"m_IndexBuffer:\s*([0-9a-fA-F]+)", txt).group(1)
    # channels: stream 0 stride? Parse m_DataSize
    dsize = int(re.search(r"m_DataSize:\s*(\d+)", txt).group(1))
    # check channels: stream 0 has pos(12)+norm(12)+tan(16) = 40
    data = bytes.fromhex(hex_v)
    idx_bytes = bytes.fromhex(hex_i)
    fmt_m = re.search(r"m_IndexFormat:\s*(\d+)", txt)
    idx_fmt = int(fmt_m.group(1)) if fmt_m else 0
    tris = np.frombuffer(idx_bytes, dtype=np.uint16 if idx_fmt == 0 else np.uint32).reshape(-1, 3)
    v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
    pos, nrm = v_raw[:, 0:3], v_raw[:, 3:6]

    p0, p1, p2 = pos[tris[:,0]], pos[tris[:,1]], pos[tris[:,2]]
    fn = np.cross(p1 - p0, p2 - p0)
    fn_u = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-8)
    vn_a = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
    dots = (fn_u * vn_a).sum(axis=1)
    centers = (p0 + p1 + p2) / 3.0
    m = (centers[:,0] > np.percentile(centers[:,0], 85)) & (np.abs(fn_u[:,0]) > 0.5)
    print(f"=== {label} verts={vc} tris={len(tris)} ===")
    print(f"  fn·vn: dot>0={(dots>0).sum()}, dot<0={(dots<0).sum()}, mean={dots.mean():.3f}")
    print(f"  Outer +X ({m.sum()}): fn.x={fn_u[m,0].mean():.3f}, vn.x={vn_a[m,0].mean():.3f}")

base = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
check_yaml_mesh(base / "cha_strongarm_gs_01.asset", "NEW cha_strongarm_gs_01")
check_yaml_mesh(base / "cha_strongarm_gs_00.asset", "NEW cha_strongarm_gs_00")
check_yaml_mesh(base / "Prowl" / "cha_prowl_official_01.asset", "OFFICIAL cha_prowl_official_01")
check_yaml_mesh(base / "Prowl" / "cha_prowl_official_00.asset", "OFFICIAL cha_prowl_official_00")
