import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

# 1. Inspect Strongarm Vehicle Mesh in bundle on specific anatomical faces (Roof top, Left/Right Outer Door)
sa_b = r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle"
env = UnityPy.load(sa_b)
for o in env.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
        pos, nrm = v_raw[:, 0:3], v_raw[:, 3:6]
        tris = np.frombuffer(bytes(mt["m_IndexBuffer"]), dtype=np.uint16).reshape(-1, 3)

        p0, p1, p2 = pos[tris[:,0]], pos[tris[:,1]], pos[tris[:,2]]
        fn = np.cross(p1 - p0, p2 - p0)
        fn_unit = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-8)
        vn_avg = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
        centers = (p0 + p1 + p2) / 3.0

        # Check Roof Top horizontal tris (Y > 2.3, |fn.y| > 0.7)
        mask_roof = (centers[:, 1] > 2.25) & (np.abs(fn_unit[:, 1]) > 0.7)
        print(f"Bundle Strongarm Roof tris ({mask_roof.sum()}):")
        if mask_roof.any():
            print(f"  fn_unit.y mean = {fn_unit[mask_roof, 1].mean():.3f} (should be +1 for up-facing in LH? Wait check Prowl!)")
            print(f"  vn_avg.y  mean = {vn_avg[mask_roof, 1].mean():.3f} (MUST BE +1 for UP-facing lighting!)")

        # Check Left/Right Outer side panels (|X| > 1.35, 0.7 < Y < 1.5)
        mask_px = (centers[:, 0] > 1.35) & (centers[:, 1] > 0.7) & (centers[:, 1] < 1.5) & (np.abs(fn_unit[:, 0]) > 0.7)
        print(f"Bundle Strongarm +X Outer side tris ({mask_px.sum()}):")
        if mask_px.any():
            print(f"  fn_unit.x mean = {fn_unit[mask_px, 0].mean():.3f}")
            print(f"  vn_avg.x  mean = {vn_avg[mask_px, 0].mean():.3f} (MUST BE +1 for +X outer side!)")
        break

# 2. Check Official Prowl Vehicle Mesh on Roof Top and +X Outer side!
pr_b = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(pr_b)
for o in env_p.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
        pos, nrm = v_raw[:, 0:3], v_raw[:, 3:6]
        tris = np.frombuffer(bytes(mt["m_IndexBuffer"]), dtype=np.uint16).reshape(-1, 3)

        p0, p1, p2 = pos[tris[:,0]], pos[tris[:,1]], pos[tris[:,2]]
        fn = np.cross(p1 - p0, p2 - p0)
        fn_unit = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-8)
        vn_avg = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
        centers = (p0 + p1 + p2) / 3.0

        mask_roof = (centers[:, 1] > 2.2) & (np.abs(fn_unit[:, 1]) > 0.7)
        print(f"\nOfficial Prowl Roof tris ({mask_roof.sum()}):")
        if mask_roof.any():
            print(f"  fn_unit.y mean = {fn_unit[mask_roof, 1].mean():.3f}")
            print(f"  vn_avg.y  mean = {vn_avg[mask_roof, 1].mean():.3f}")

        mask_px = (centers[:, 0] > 1.45) & (centers[:, 1] > 0.5) & (centers[:, 1] < 1.5) & (np.abs(fn_unit[:, 0]) > 0.7)
        print(f"Official Prowl +X Outer side tris ({mask_px.sum()}):")
        if mask_px.any():
            print(f"  fn_unit.x mean = {fn_unit[mask_px, 0].mean():.3f}")
            print(f"  vn_avg.x  mean = {vn_avg[mask_px, 0].mean():.3f}")
        break

# 3. Also check Strongarm Robot Head/Chest +Y/+X/+Z vs Official Prowl Robot!
for label, bpath in [("Bundle Strongarm Robot", sa_b), ("Official Prowl Robot", pr_b)]:
    ev = UnityPy.load(bpath)
    for o in ev.objects:
        if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_00":
            mt = o.read_typetree()
            vc = mt["m_VertexData"]["m_VertexCount"]
            data = bytes(mt["m_VertexData"]["m_DataSize"])
            v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
            pos, nrm = v_raw[:, 0:3], v_raw[:, 3:6]
            tris = np.frombuffer(bytes(mt["m_IndexBuffer"]), dtype=np.uint16).reshape(-1, 3)
            p0, p1, p2 = pos[tris[:,0]], pos[tris[:,1]], pos[tris[:,2]]
            fn = np.cross(p1 - p0, p2 - p0)
            fn_unit = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-8)
            vn_avg = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
            centers = (p0 + p1 + p2) / 3.0
            # Check shoulders outer +X > 2.2
            m = (centers[:, 0] > 2.0) & (np.abs(fn_unit[:, 0]) > 0.7)
            print(f"\n{label} Outer +X shoulder tris ({m.sum()}): fn.x={fn_unit[m,0].mean():.3f}, vn.x={vn_avg[m,0].mean():.3f}")
            break
