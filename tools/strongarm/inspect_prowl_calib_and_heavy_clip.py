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

prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)

# 1. Inspect Official Prowl Vehicle SMR materials & SubMesh count
for o in env_p.objects:
    if o.type.name == "SkinnedMeshRenderer":
        st = o.read_typetree()
        m_pid = st["m_Mesh"]["m_PathID"]
        for o2 in env_p.objects:
            if o2.path_id == m_pid:
                mt = o2.read_typetree()
                if mt.get("m_Name") == "cha_prowl_gs_deluxe2016_01":
                    mat_names = []
                    for mp in st["m_Materials"]:
                        for o3 in env_p.objects:
                            if o3.path_id == mp["m_PathID"]:
                                mat_t = o3.read_typetree()
                                base_st = [(t[1]["m_Scale"], t[1]["m_Offset"]) for t in mat_t["m_SavedProperties"]["m_TexEnvs"] if t[0] == "_base_tex"]
                                mat_names.append((o3.path_id, mat_t["m_Name"], base_st))
                                break
                    print("Official Prowl Vehicle SMR Materials:", mat_names)
                    print("Official Prowl Vehicle SubMeshes:", len(mt["m_SubMeshes"]))
                    break

# 2. Sample Official Prowl Vehicle RAOE and NM conditioned on Albedo brightness (white paint vs black trim/tires vs red/blue lights)
texs = {}
for o in env_p.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        texs[t.m_Name] = np.array(t.image.convert("RGBA"))

ta = texs["tform_misc_A"]
tn = texs["tform_misc_NM"]
tr = texs["main_tform_misc_RAOE"]
# Mat 8471270994157717165: _base_tex top half (PIL y=0..256), _pbr_composite_tex bottom-right quad (PIL y=256..512, x=256..512)
a_vh = ta[0:256, :, :3]
n_vh = tn[0:256, :, :3]
# Resize bottom-right quad (256x256) to (256, 512) matching top half (H=256, W=512)!
r_vh = np.array(Image.fromarray(tr[256:512, 256:512, :3]).resize((512, 256), Image.BILINEAR))

white_mask = (a_vh[:,:,0] > 180) & (a_vh[:,:,1] > 180) & (a_vh[:,:,2] > 180)
dark_mask  = (a_vh[:,:,0] < 50) & (a_vh[:,:,1] < 50) & (a_vh[:,:,2] < 50)
mid_mask   = (a_vh[:,:,0] > 70) & (a_vh[:,:,0] < 160) & (np.abs(a_vh[:,:,0].astype(int)-a_vh[:,:,2].astype(int)) < 20)

print("\n=== Official Prowl Vehicle Surface Calibration ===")
for name, mask in [("White Paint (>180)", white_mask), ("Black Trim/Tires (<50)", dark_mask), ("Grey Metal (70-160)", mid_mask)]:
    print(f"  {name} (px={mask.sum()}): RAOE.R(Rough)={r_vh[mask,0].mean():.1f}, RAOE.G(AO)={r_vh[mask,1].mean():.1f}, RAOE.B(Emis)={r_vh[mask,2].mean():.1f}, NM.B(Metal)={n_vh[mask,2].mean():.1f}")

# 3. Inspect Strongarm Raw OBJ wheel centers and axle positions using Blender-equivalent rotation
obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
vs = []
for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("v "):
        x, y, z = [float(p) for p in line.split()[1:4]]
        # Match Blender step A: rot +90 X -> (x, -z, y)!! Wait: cos90=0, sin90=1 -> (x, -z, y)
        vs.append((x, -z, y))
vs = np.array(vs)
print("\n=== Raw OBJ rotated +90X (Blender Z-up: X=side, Y=front/back, Z=height) ===")
print(f"  X=[{vs[:,0].min():.3f}, {vs[:,0].max():.3f}] w={np.ptp(vs[:,0]):.3f}")
print(f"  Y=[{vs[:,1].min():.3f}, {vs[:,1].max():.3f}] l={np.ptp(vs[:,1]):.3f}")
print(f"  Z=[{vs[:,2].min():.3f}, {vs[:,2].max():.3f}] h={np.ptp(vs[:,2]):.3f}")

# Find tire bottom vertices (Z < 0.25) in each quadrant to find exact raw wheel centers!
for qname, mx, my in [("Front(+Y)/Left(+X)?", vs[:,0]>0.5, vs[:,1]>0.5),
                      ("Front(+Y)/Right(-X)?", vs[:,0]<-0.5, vs[:,1]>0.5),
                      ("Rear(-Y)/Left(+X)?", vs[:,0]>0.5, vs[:,1]<-0.5),
                      ("Rear(-Y)/Right(-X)?", vs[:,0]<-0.5, vs[:,1]<-0.5)]:
    m = mx & my & (vs[:,2] < 0.7)
    pts = vs[m]
    # Check outer ring near tire bottom/top
    zmin, zmax = pts[:,2].min(), pts[:,2].max()
    ymin, ymax = pts[:,1].min(), pts[:,1].max()
    #Wait wheel bottom Z and max radius along Y!
    low = pts[pts[:,2] < 0.35]
    print(f"  {qname}: lowZ min={zmin:.3f}, Y_low_center={low[:,1].mean():.3f} (Y range in Z<0.35: [{low[:,1].min():.3f}, {low[:,1].max():.3f}])")

# 4. Also check AnimationClip 'Car_Prowl_Normal_attackHeavy_transformed' for CenterBackCarFront vs COG vs Wheel*_T!
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

all_crc = {}
def collect_subpaths(tid, parts):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    cur = parts + [nm]
    for k in range(len(cur)):
        sub = "/".join(cur[k:])
        all_crc[zlib.crc32(sub.encode("utf-8")) & 0xFFFFFFFF] = sub
    for cid in children_map.get(tid, []):
        collect_subpaths(cid, cur)

for tid, tr in tr_by_id.items():
    if tr["m_Father"]["m_PathID"] == 0 and go_name.get(tr["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        collect_subpaths(tid, [])

for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        if ct.get("m_Name") == "Car_Prowl_Normal_attackHeavy_transformed":
            print("\n=== Car_Prowl_Normal_attackHeavy_transformed MID-CLIP (frame 25/52) ===")
            gbs = ct["m_ClipBindingConstant"]["genericBindings"]
            d = ct["m_MuscleClip"]["m_Clip"]["data"]
            const_arr = d["m_ConstantClip"]["data"]
            dense = d["m_DenseClip"]
            s_cnt = d["m_StreamedClip"]["curveCount"]
            d_cnt = dense["m_CurveCount"]
            d_frames = dense["m_FrameCount"]
            d_arr = dense["m_SampleArray"]
            attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
            cidx = 0
            for gb in gbs:
                p = all_crc.get(gb["path"], f"CRC:{gb['path']}")
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                if s_cnt <= cidx < s_cnt + d_cnt:
                    di = cidx - s_cnt
                    f0 = [round(d_arr[di + k], 3) for k in range(dim)]
                    fm = [round(d_arr[(d_frames//2)*d_cnt + di + k], 3) for k in range(dim)]
                    fe = [round(d_arr[(d_frames-1)*d_cnt + di + k], 3) for k in range(dim)]
                    if any(k in p for k in ("CenterBackCarFront", "COG", "Wheel", "BodyBase", "CenterRoof")):
                        print(f"  attr={attr} {p:48s} f0={f0} mid={fm} end={fe}")
                cidx += dim
            break
