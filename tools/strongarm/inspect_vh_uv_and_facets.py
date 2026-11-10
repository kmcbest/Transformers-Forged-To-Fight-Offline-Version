import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import UnityPy
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# 1. Check frontend_Prowl_levelup_vehicle_idle_transformed with stripped 'character_model/' prefix
prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)

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
    if p.startswith("character_model/"):
        sub = p[len("character_model/"):]
        crc_to_path[zlib.crc32(sub.encode("utf-8")) & 0xFFFFFFFF] = sub
    for cid in children_map.get(tid, []):
        walk(cid, p)

for rtid in roots:
    if go_name.get(tr_by_id[rtid]["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        for cid in children_map.get(rtid, []):
            walk(cid, "")

print("=== Checking AnimationClip tracks with stripped prefix ===")
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if nm in ("frontend_Prowl_levelup_vehicle_idle_transformed",):
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
            for idx, gb in enumerate(gbs):
                p = crc_to_path.get(gb["path"], f"CRC:{gb['path']}")
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                if cidx < s_cnt:
                    src = "STREAM"
                elif cidx < s_cnt + d_cnt:
                    di = cidx - s_cnt
                    src = f"DENSE {[round(d_arr[di + k], 4) for k in range(dim)]}"
                else:
                    ci = cidx - (s_cnt + d_cnt)
                    src = f"CONST {[round(x, 4) for x in const_arr[ci:ci+dim]]}"
                # Print all attr=3 (scale), or any COG / CenterBackCarFront / Wheel / Reference
                if attr == 3 or any(k in p for k in ("CenterBackCarFront", "COG", "Wheel", "CenterRoof", "Reference")):
                    print(f"  [{idx:2d}] attr={attr} {p:45s} -> {src}")
                cidx += dim

# 2. Check Strongarm vehicle mesh inside strongarm_gs.assetbundle: vertex welding, face normals, roof & hood UVs
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
for o in env_s.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
        pos = v_raw[:, 0:3]
        nrm = v_raw[:, 3:6]
        tan = v_raw[:, 6:10]
        uv = np.frombuffer(data[vc*40 : vc*48], dtype="<f4").reshape(vc, 2)
        tris = np.frombuffer(bytes(mt["m_IndexBuffer"]), dtype=np.uint16).reshape(-1, 3)

        # Count unique positions on body (Bone 0 -> first 2192 verts? Let's check weights/bones stream)
        # Body triangles are those whose vertices have high Y or |Z|>2.5 or let's read bone stream
        bone_stream = np.frombuffer(data[vc*48 : vc*80], dtype="<u4").reshape(vc, 8)
        bone0 = bone_stream[:, 4] # 4 weights float32, then 4 uint32 bone indices
        body_mask = (bone0 == 0)
        print(f"\n=== Strongarm Vehicle Mesh Diagnostics ===")
        print(f"Total verts={vc}, body verts={body_mask.sum()}, wheel verts={(~body_mask).sum()}")
        body_pos = pos[body_mask]
        # How many unique 3D positions exist in body?
        rounded = np.round(body_pos, 4)
        uniq_pos, inv = np.unique(rounded, axis=0, return_inverse=True)
        print(f"Body unique spatial positions: {len(uniq_pos)} vs {len(body_pos)} vertices (avg copies per pos: {len(body_pos)/len(uniq_pos):.2f})")

        # Measure normal divergence at shared spatial positions on the body!
        divs = []
        max_divs = []
        body_nrm = nrm[body_mask]
        for uid in range(len(uniq_pos)):
            idxs = np.where(inv == uid)[0]
            if len(idxs) > 1:
                dots = body_nrm[idxs] @ body_nrm[idxs].T
                min_dot = float(np.clip(dots.min(), -1.0, 1.0))
                ang = float(np.degrees(np.arccos(min_dot)))
                if ang > 5.0:
                    max_divs.append(ang)
        print(f"Body shared positions with >5 deg split normals: {len(max_divs)} / {len(uniq_pos)} (max split angle={max(max_divs) if max_divs else 0:.1f} deg)")

        # Check front hood & roof lightbar triangle UVs and positions
        # Remember in Unity: X=right/left, Y=up, Z=front(+)/back(-) or back(+)/front(-)!
        # Let's check where hood & lightbar are in Z!
        print(f"Body Y max={body_pos[:,1].max():.3f}, Z=[{body_pos[:,2].min():.3f}, {body_pos[:,2].max():.3f}]")
        # Check roof (Y > 2.2) tris and draw in BLUE on a copy of UV overlay, Hood (1.2<Y<1.8, Z>1.0 vs Z<-1.0)
        im = Image.open(SCRATCH / "bundle_tform_misc_A.png").convert("RGB").resize((1024, 1024))
        dr = ImageDraw.Draw(im)
        for t0, t1, t2 in tris:
            pts_3d = pos[[t0, t1, t2]]
            yc = pts_3d[:, 1].mean()
            zc = pts_3d[:, 2].mean()
            if yc > 2.38:  # Very top roof/lightbar
                col = (255, 0, 255) # magenta = roof lightbar / top roof
            elif 1.15 < yc < 1.85 and zc < -1.0:
                col = (255, 255, 0) # yellow = Z<-1.0
            elif 1.15 < yc < 1.85 and zc > 1.0:
                col = (0, 255, 255) # cyan = Z>+1.0
            else:
                continue
            pts_uv = [(uv[i,0]*1024, (1.0 - uv[i,1])*1024) for i in (t0, t1, t2)]
            dr.polygon(pts_uv, outline=col)
        im.save(SCRATCH / "verify_vh_regions_uv.png")
        print("Saved scratch/verify_vh_regions_uv.png (Magenta=Y>2.38 roof/lightbar, Yellow=Z<-1, Cyan=Z>+1)")
        break
