import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from pathlib import Path

def check_mesh_winding(bundle_path, mesh_name, label):
    env = UnityPy.load(bundle_path)
    for o in env.objects:
        if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == mesh_name:
            mt = o.read_typetree()
            vc = mt["m_VertexData"]["m_VertexCount"]
            data = bytes(mt["m_VertexData"]["m_DataSize"])
            channels = mt["m_VertexData"]["m_Channels"]
            # Find stream 0 stride
            s0_stride = max(c["offset"] + c["dimension"]*4 for c in channels if c["dimension"] > 0 and c["stream"] == 0)
            v_raw = np.frombuffer(data[:vc*s0_stride], dtype="<f4").reshape(vc, s0_stride // 4)
            pos = v_raw[:, 0:3]
            nrm = v_raw[:, 3:6]
            idx_bytes = bytes(mt["m_IndexBuffer"])
            fmt_idx = mt.get("m_IndexFormat", 0)
            tris = np.frombuffer(idx_bytes, dtype=np.uint16 if fmt_idx == 0 else np.uint32).reshape(-1, 3)

            p0, p1, p2 = pos[tris[:,0]], pos[tris[:,1]], pos[tris[:,2]]
            fn = np.cross(p1 - p0, p2 - p0)
            fn_len = np.linalg.norm(fn, axis=1, keepdims=True)
            fn_unit = fn / np.maximum(fn_len, 1e-8)
            vn_avg = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
            dots = (fn_unit * vn_avg).sum(axis=1)

            # Check centroid normal test (from mesh center outward)
            center = np.array([0.0, (pos[:,1].min()+pos[:,1].max())/2, 0.0])
            tri_c = (p0 + p1 + p2) / 3.0 - center
            out_dot_vn = (tri_c * vn_avg).sum(axis=1)
            out_dot_fn = (tri_c * fn_unit).sum(axis=1)

            print(f"\n=== {label} ({mesh_name}) verts={vc} tris={len(tris)} ===")
            print(f"  pos X=[{pos[:,0].min():.3f},{pos[:,0].max():.3f}] Y=[{pos[:,1].min():.3f},{pos[:,1].max():.3f}] Z=[{pos[:,2].min():.3f},{pos[:,2].max():.3f}]")
            print(f"  fn·vn: dot>0={(dots>0).sum()}, dot<0={(dots<0).sum()}, mean={dots.mean():.3f}")
            print(f"  outward·vn: >0={(out_dot_vn>0).sum()}, <0={(out_dot_vn<0).sum()}")
            print(f"  outward·fn: >0={(out_dot_fn>0).sum()}, <0={(out_dot_fn<0).sum()}")

            # Also check shared positions vs split normals
            uniq_p, inv = np.unique(np.round(pos, 4), axis=0, return_inverse=True)
            split_cnt = 0
            for uid in range(len(uniq_p)):
                idxs = np.where(inv == uid)[0]
                if len(idxs) > 1:
                    d = nrm[idxs] @ nrm[idxs].T
                    if d.min() < np.cos(np.radians(45)):
                        split_cnt += 1
            print(f"  unique_pos={len(uniq_p)}/{vc} (ratio={vc/len(uniq_p):.2f}), >45deg_splits={split_cnt}")
            break

prowl_b = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
sa_b = r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle"

check_mesh_winding(prowl_b, "cha_prowl_gs_deluxe2016_01", "Official Prowl Vehicle")
check_mesh_winding(sa_b, "cha_prowl_gs_deluxe2016_01", "Strongarm Vehicle")
check_mesh_winding(prowl_b, "cha_prowl_gs_deluxe2016_00", "Official Prowl Robot")
check_mesh_winding(sa_b, "cha_prowl_gs_deluxe2016_00", "Strongarm Robot")
