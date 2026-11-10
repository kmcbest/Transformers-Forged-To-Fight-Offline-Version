import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import UnityPy
import numpy as np
from pathlib import Path
from PIL import Image

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# 1. Inspect Official Prowl vehicle textures & Robot vs Vehicle RAOE / NM pixel distributions
prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)

p_tex = {}
for o in env_p.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        p_tex[t.m_Name] = np.array(t.image.convert("RGBA"))

if "main_tform_misc_RAOE" in p_tex:
    pr = p_tex["main_tform_misc_RAOE"]
    H, W, _ = pr.shape
    # Check Vehicle quadrant (Mat 8471270994157717165: Scale(0.5, 0.5), Offset(0.5, 0.0) -> Unity u=[0.5..1.0], v=[0.0..0.5] -> PIL x=[0.5W..W], y=[0.5H..H])
    vh_q = pr[H//2:H, W//2:W]
    Image.fromarray(vh_q).save(SCRATCH / "prowl_official_vh_RAOE_quad.png")
    print("Official Prowl Vehicle RAOE quad (u=0.5..1, v=0..0.5):")
    for i, c in enumerate(["R", "G", "B", "A"]):
        arr = vh_q[:, :, i]
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])
        print(f"  {c}: min={arr.min()} p10={p10:.1f} p50={p50:.1f} p90={p90:.1f} max={arr.max()} mean={arr.mean():.1f}")

if "tform_misc_NM" in p_tex:
    pn = p_tex["tform_misc_NM"]
    H, W, _ = pn.shape
    # Top half is Prowl Car NM (Offset y=0.5, Scale y=0.5 -> PIL y=0..H//2)
    vh_nm = pn[0:H//2, :]
    Image.fromarray(vh_nm).save(SCRATCH / "prowl_official_vh_NM_top.png")
    print("Official Prowl Vehicle NM top half:")
    for i, c in enumerate(["R", "G", "B", "A"]):
        arr = vh_nm[:, :, i]
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])
        print(f"  {c}: min={arr.min()} p10={p10:.1f} p50={p50:.1f} p90={p90:.1f} max={arr.max()} mean={arr.mean():.1f}")

# 2. Check CRC hashes with EVERY possible prefix depth in Prowl_GS_Deluxe2016
tr_by_id = {}
go_name = {}
animators = []
for o in env_p.objects:
    if o.type.name == "GameObject":
        go_name[o.path_id] = o.read_typetree().get("m_Name", "")
    elif o.type.name == "Transform":
        tr_by_id[o.path_id] = o.read_typetree()
    elif o.type.name == "Animator":
        animators.append(o.read_typetree())

print("\nAnimators in Prowl bundle:")
for a in animators:
    go_n = go_name.get(a["m_GameObject"]["m_PathID"], "?")
    print("  Animator on GO:", go_n, "m_Avatar:", a["m_Avatar"])

children_map = {}
for tid, tr in tr_by_id.items():
    for c in tr["m_Children"]:
        children_map.setdefault(tid, []).append(c["m_PathID"])

# Generate all suffix subpaths
all_crc = {}
def collect_subpaths(tid, parts):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    cur = parts + [nm]
    for k in range(len(cur)):
        sub = "/".join(cur[k:])
        h = zlib.crc32(sub.encode("utf-8")) & 0xFFFFFFFF
        all_crc[h] = sub
    for cid in children_map.get(tid, []):
        collect_subpaths(cid, cur)

for tid, tr in tr_by_id.items():
    if tr["m_Father"]["m_PathID"] == 0 and go_name.get(tr["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        collect_subpaths(tid, [])

for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        if ct.get("m_Name") == "frontend_Prowl_levelup_vehicle_idle_transformed":
            gbs = ct["m_ClipBindingConstant"]["genericBindings"]
            d = ct["m_MuscleClip"]["m_Clip"]["data"]
            const_arr = d["m_ConstantClip"]["data"]
            dense = d["m_DenseClip"]
            streamed = d["m_StreamedClip"]
            s_cnt = streamed["curveCount"]
            d_cnt = dense["m_CurveCount"]
            d_arr = dense["m_SampleArray"]
            attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
            cidx = 0
            print("\n=== frontend_Prowl_levelup_vehicle_idle_transformed ALL Pos/Rot/Scale ===")
            for idx, gb in enumerate(gbs):
                p = all_crc.get(gb["path"], f"CRC:{gb['path']}")
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                if cidx < s_cnt:
                    src = "STREAM"
                elif cidx < s_cnt + d_cnt:
                    di = cidx - s_cnt
                    src = f"DENSE f0={[round(d_arr[di+k],4) for k in range(dim)]}"
                else:
                    ci = cidx - (s_cnt + d_cnt)
                    src = f"CONST {[round(x,4) for x in const_arr[ci:ci+dim]]}"
                if any(k in p for k in ("CenterBackCarFront", "COG", "Wheel", "CenterRoof", "Hips", "transformed")):
                    print(f"  attr={attr} {p:45s} -> {src}")
                cidx += dim
            break

# 3. Check Strongarm vehicle mesh winding vs normals in strongarm_gs.assetbundle
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
for o in env_s.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
        pos = v_raw[:, 0:3]
        nrm = v_raw[:, 3:6]
        tris = np.frombuffer(bytes(mt["m_IndexBuffer"]), dtype=np.uint16).reshape(-1, 3)

        p0 = pos[tris[:,0]]
        p1 = pos[tris[:,1]]
        p2 = pos[tris[:,2]]
        # In Unity (left-handed): front-face winding (t0, t1, t2) clockwise from outside -> (p1-p0) x (p2-p0) points IN THE NORMAL DIRECTION!
        # Let's verify dot product of (p1-p0)x(p2-p0) with vertex normals AND check outward normal direction!
        fn = np.cross(p1 - p0, p2 - p0)
        fn_len = np.linalg.norm(fn, axis=1, keepdims=True)
        fn_unit = fn / np.maximum(fn_len, 1e-8)
        vn_avg = (nrm[tris[:,0]] + nrm[tris[:,1]] + nrm[tris[:,2]]) / 3.0
        dots = (fn_unit * vn_avg).sum(axis=1)
        print(f"\n=== Strongarm Vehicle Mesh Triangle Winding vs Vertex Normals ===")
        print(f"  Tris={len(tris)}, dot>0 (matches LH CW): {(dots>0).sum()}, dot<0: {(dots<0).sum()}, min={dots.min():.3f}, max={dots.max():.3f}")
        # Check roof triangles pointing up (+Y)
        roof_mask = ((p0[:,1]+p1[:,1]+p2[:,1])/3.0 > 2.3) & (np.abs(fn_unit[:,1]) > 0.7)
        if roof_mask.any():
            print(f"  Roof horizontal tris={roof_mask.sum()}: mean fn_unit.y={fn_unit[roof_mask,1].mean():.3f}, mean vn_avg.y={vn_avg[roof_mask,1].mean():.3f}")
        break
