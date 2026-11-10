import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import struct
import UnityPy
import numpy as np
from pathlib import Path

prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)

# 1. Build CRC32 -> path map for Prowl_GS_Deluxe2016
tr_by_id = {}
go_name = {}
for o in env_p.objects:
    if o.type.name == "GameObject":
        go_name[o.path_id] = o.read_typetree().get("m_Name", "")
    elif o.type.name == "Transform":
        tr_by_id[o.path_id] = o.read_typetree()

children_map = {}
for tid, tr in tr_by_id.items():
    for c in tr["m_Children"]:
        children_map.setdefault(tid, []).append(c["m_PathID"])

roots = [tid for tid, tr in tr_by_id.items() if tr["m_Father"]["m_PathID"] == 0]
crc_to_path = {}
def walk(tid, prefix):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    p = nm if not prefix else f"{prefix}/{nm}"
    crc_to_path[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = p
    for cid in children_map.get(tid, []):
        walk(cid, p)

for rtid in roots:
    if go_name.get(tr_by_id[rtid]["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        for cid in children_map.get(rtid, []):
            walk(cid, "")

# 2. Decode DenseClip & ConstantClip curves for vehicle AnimationClips
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if nm in ("frontend_Prowl_levelup_vehicle_idle_transformed", "frontend_Prowl_levelup_enter_transformed", "Car_Prowl_Normal_attackHeavy_transformed"):
            print(f"\n=== Clip: {nm} ===")
            gbs = ct["m_ClipBindingConstant"]["genericBindings"]
            d = ct["m_MuscleClip"]["m_Clip"]["data"]
            const_arr = d["m_ConstantClip"]["data"]
            dense = d["m_DenseClip"]
            streamed = d["m_StreamedClip"]
            s_cnt = streamed["curveCount"]
            d_cnt = dense["m_CurveCount"]
            d_frames = dense["m_FrameCount"]
            d_arr = dense["m_SampleArray"]
            # Check what each curve corresponds to
            attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
            print(f"  streamed={s_cnt}, dense={d_cnt} (frames={d_frames}), const={len(const_arr)}, total_gb={len(gbs)}")
            cidx = 0
            for gb in gbs:
                p = crc_to_path.get(gb["path"], f"CRC:{gb['path']}")
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                if cidx < s_cnt:
                    src = "STREAM"
                    val = None
                elif cidx < s_cnt + d_cnt:
                    di = cidx - s_cnt
                    f0 = [round(d_arr[di + k], 4) for k in range(dim)]
                    flast = [round(d_arr[(d_frames - 1)*d_cnt + di + k], 4) for k in range(dim)]
                    src = f"DENSE f0={f0} fLast={flast}"
                else:
                    ci = cidx - (s_cnt + d_cnt)
                    cval = [round(x, 4) for x in const_arr[ci:ci+dim]]
                    src = f"CONST {cval}"
                if any(k in str(p) for k in ("CenterBackCarFront", "COG", "Wheel", "CenterRoof", "Reference")):
                    print(f"  attr={attr} {p:45s} -> {src}")
                cidx += dim

# 3. Inspect raw strongarm_vehicle.obj vertices, UVs, and connected components / bounds
obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
vs, vns, vts, faces = [], [], [], []
for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("v "):
        vs.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("vt "):
        vts.append([float(x) for x in line.split()[1:3]])
    elif line.startswith("vn "):
        vns.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("f "):
        faces.append(line.split()[1:])

vs = np.array(vs)
vts = np.array(vts)
vns = np.array(vns) if vns else None
print(f"\n=== Raw OBJ stats ===")
print(f"  v={len(vs)}, vt={len(vts)}, vn={len(vns) if vns is not None else 0}, f={len(faces)}")
print(f"  Raw OBJ coords (X=width, Y=height, Z=length):")
print(f"    X: [{vs[:,0].min():.4f}, {vs[:,0].max():.4f}] size={vs[:,0].max()-vs[:,0].min():.4f}")
print(f"    Y: [{vs[:,1].min():.4f}, {vs[:,1].max():.4f}] size={vs[:,1].max()-vs[:,1].min():.4f}")
print(f"    Z: [{vs[:,2].min():.4f}, {vs[:,2].max():.4f}] size={vs[:,2].max()-vs[:,2].min():.4f}")

# Check UV bounds of triangles near top of roof (lightbar vs cab)
lightbar_uvs = []
hood_uvs = []
for f in faces:
    v_idx = [int(tok.split("/")[0]) - 1 for tok in f]
    vt_idx = [int(tok.split("/")[1]) - 1 for tok in f if "/" in tok and tok.split("/")[1]]
    pts = vs[v_idx]
    if pts[:,1].mean() > 2.2: # Topmost lightbar
        for ti in vt_idx:
            lightbar_uvs.append(vts[ti])
    elif 1.1 < pts[:,1].mean() < 1.6 and pts[:,2].mean() < -1.0: # Hood? Wait check Z sign!
        for ti in vt_idx:
            hood_uvs.append(vts[ti])

if lightbar_uvs:
    luv = np.array(lightbar_uvs)
    print(f"  Top lightbar (Y>2.2) UV range: u=[{luv[:,0].min():.3f}, {luv[:,0].max():.3f}] v=[{luv[:,1].min():.3f}, {luv[:,1].max():.3f}]")
print(f"  Note: Which Z is front in raw OBJ? Min Z vs Max Z width/height at front/back:")
front_neg = vs[vs[:,2] < -2.0]
front_pos = vs[vs[:,2] > 2.0]
print(f"    Z<-2.0: Y max={front_neg[:,1].max():.3f}, count={len(front_neg)}")
print(f"    Z>+2.0: Y max={front_pos[:,1].max():.3f}, count={len(front_pos)}")
