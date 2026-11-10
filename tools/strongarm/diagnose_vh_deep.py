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

# 1. Crop phone screenshots to inspect pixels clearly
for src_name, dst_name, box in [
    (r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\.user_uploaded\media_1794318101704_e9c20527.jpg", "crop_phone_vh_side.png", (320, 420, 740, 700)),
    (r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\.user_uploaded\media_1794318135552_25055754.jpg", "crop_phone_vh_front.png", (380, 400, 700, 690)),
]:
    im = Image.open(src_name)
    w, h = im.size
    # scale coords proportionally in case resolution isn't 1000x...
    sx, sy = w / 1000.0, h / 450.0  # let's check actual image size first
    print(dst_name, "orig size:", im.size)
    # Use normalized fraction crop for middle-bottom area where vehicle sits
    c = im.crop((int(w*0.33), int(h*0.56), int(w*0.72), int(h*0.99)))
    c.save(SCRATCH / dst_name)

# 2. Check Prowl official bundle Materials and AnimationClip bindings
prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)
print("\n=== Official Prowl Materials ===")
for o in env_p.objects:
    if o.type.name == "Material":
        mt = o.read_typetree()
        texs = {t[0]: (t[1]["m_Scale"], t[1]["m_Offset"], t[1]["m_Texture"]["m_PathID"]) for t in mt["m_SavedProperties"]["m_TexEnvs"] if t[1]["m_Texture"]["m_PathID"] != 0}
        print(f"Mat {o.path_id} ({mt['m_Name']}):", texs)

# 3. Map CRC32 transform path hashes in Prowl's rig to decode AnimationClip bindings
# Build GameObject path map in Prowl_GS_Deluxe2016
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

# Find roots
roots = [tid for tid, tr in tr_by_id.items() if tr["m_Father"]["m_PathID"] == 0]
crc_to_path = {}
def walk(tid, prefix):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    p = nm if prefix is None else (f"{prefix}/{nm}" if prefix else nm)
    # Unity path hashes relative to Animator root (so root's name isn't included, wait include both!)
    crc_to_path[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = p
    crc_to_path[zlib.crc32(nm.encode("utf-8")) & 0xFFFFFFFF] = f"({nm})"
    for cid in children_map.get(tid, []):
        walk(cid, p)

for rtid in roots:
    nm = go_name.get(tr_by_id[rtid]["m_GameObject"]["m_PathID"], "")
    print(f"Root Transform {rtid}: {nm}")
    # relative paths under Animator root
    for cid in children_map.get(rtid, []):
        walk(cid, "")

print(f"Mapped {len(crc_to_path)} CRC paths.")

# Inspect AnimationClips in official Prowl
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if nm in ("frontend_Prowl_levelup_vehicle_idle_transformed", "frontend_Prowl_levelup_enter_transformed", "Car_Prowl_Normal_attackHeavy_transformed"):
            print(f"\n=== Clip: {nm} ===")
            gbs = ct["m_ClipBindingConstant"]["genericBindings"]
            # Attribute: 1=Pos, 2=Rot, 3=Scale, 4=Euler
            # Let's check streamedClip / denseClip / constantClip
            mclip = ct["m_MuscleClip"]["m_Clip"]
            data_blob = mclip.get("m_ConstantClip", {}).get("data", [])
            dense = mclip.get("m_DenseClip", {})
            streamed = mclip.get("m_StreamedClip", {})
            print(f"  bindings={len(gbs)}, constLen={len(data_blob)}, denseCurves={dense.get('m_CurveCount')}, denseFrames={dense.get('m_FrameCount')}, streamedCurves={streamed.get('curveCount')}")
            # Find curve index per genericBinding (Transform attrs take 3, 4, 3, 3 floats!)
            attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
            curve_idx = 0
            # Note: Streamed curves come first, then Dense curves, then Constant curves!
            s_cnt = streamed.get("curveCount", 0)
            d_cnt = dense.get("m_CurveCount", 0)
            for gb in gbs:
                p = crc_to_path.get(gb["path"], f"CRC:{gb['path']}")
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                # Which storage?
                vals = None
                if curve_idx >= s_cnt + d_cnt:
                    ci = curve_idx - (s_cnt + d_cnt)
                    vals = data_blob[ci:ci+dim]
                    src = "CONST"
                elif curve_idx >= s_cnt:
                    di = curve_idx - s_cnt
                    # sample frame 0
                    vals = dense["m_SampleArray"][di:di+dim]
                    src = "DENSE0"
                else:
                    src = "STREAM"
                if any(k in str(p) for k in ("CenterBackCarFront", "COG", "Wheel", "CenterRoof", "Root", "Master")):
                    print(f"  attr={attr} ({src}) path={p} vals={vals}")
                curve_idx += dim

# 4. Inspect strongarm_gs.assetbundle texture -1377069345250401912 (RAOE) and 7289807295065357004 (NM)
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
for o in env_s.objects:
    if o.type.name == "Texture2D" and o.path_id in (-1377069345250401912, 7289807295065357004, -3877080133234792206):
        t = o.read()
        print(f"\nBundle Texture {o.path_id} name={t.m_Name} size=({t.m_Width},{t.m_Height}) fmt={t.m_TextureFormat}")
        im = t.image
        if o.path_id == -1377069345250401912:
            im.save(SCRATCH / "bundle_tform_misc_RAOE.png")
            print("Saved scratch/bundle_tform_misc_RAOE.png")
        elif o.path_id == 7289807295065357004:
            im.save(SCRATCH / "bundle_tform_misc_NM_check.png")
