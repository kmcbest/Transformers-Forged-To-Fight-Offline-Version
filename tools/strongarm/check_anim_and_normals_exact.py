import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import UnityPy
import numpy as np
from pathlib import Path

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
all_paths = []
def walk(tid, prefix):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    p = nm if not prefix else f"{prefix}/{nm}"
    all_paths.append(p)
    crc_to_path[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = p
    for cid in children_map.get(tid, []):
        walk(cid, p)

for rtid in roots:
    if go_name.get(tr_by_id[rtid]["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        for cid in children_map.get(rtid, []):
            walk(cid, "")

print("Sample rig paths:", all_paths[:15])

# Find what paths exist in frontend_Prowl_levelup_vehicle_idle_transformed
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if nm in ("frontend_Prowl_levelup_vehicle_idle_transformed", "Car_Prowl_Normal_attackHeavy_transformed"):
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
            attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
            cidx = 0
            matched = 0
            for idx, gb in enumerate(gbs):
                p = crc_to_path.get(gb["path"], f"CRC:{gb['path']}")
                if not p.startswith("CRC:"):
                    matched += 1
                attr = gb["attribute"]
                dim = attr_dims.get(attr, 1)
                if cidx < s_cnt:
                    src = "STREAM"
                elif cidx < s_cnt + d_cnt:
                    di = cidx - s_cnt
                    f0 = [round(d_arr[di + k], 4) for k in range(dim)]
                    src = f"DENSE f0={f0}"
                else:
                    ci = cidx - (s_cnt + d_cnt)
                    cval = [round(x, 4) for x in const_arr[ci:ci+dim]]
                    src = f"CONST {cval}"
                if idx < 30 or any(k in p for k in ("CenterBackCarFront", "COG", "Wheel")):
                    print(f"  [{idx:2d}] attr={attr} typeId={gb.get('typeID')} {p:45s} -> {src}")
                cidx += dim
            print(f"  matched={matched}/{len(gbs)}")

# Also check Cha_strongarm_gs_01 materials & normals from unity_build_project/Assets/Strongarm
sa_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
print("\n=== Files in Assets/Strongarm ===")
for f in sorted(sa_dir.iterdir()):
    if f.is_file():
        print(" ", f.name, f.stat().st_size)
        if f.suffix == ".mat":
            txt = f.read_text(encoding="utf-8", errors="ignore")
            for line in txt.splitlines():
                if any(k in line for k in ("m_Name:", "_Metallic", "_Gloss", "_Bump", "_Color", "_Emission", "m_Scale", "m_Offset", "_MainTex")):
                    print("   ", line.strip())

# Check Prowl_GS_Deluxe2016 prefab hierarchy for vehicle SMR parent & local scale
print("\n=== Vehicle SMR Transform in Official Prowl_GS_Deluxe2016 ===")
for o in env_p.objects:
    if o.type.name == "SkinnedMeshRenderer":
        st = o.read_typetree()
        m_pid = st["m_Mesh"]["m_PathID"]
        m_name = ""
        for o2 in env_p.objects:
            if o2.path_id == m_pid:
                m_name = o2.read_typetree().get("m_Name", "")
                break
        if "_01" in m_name:
            go_pid = st["m_GameObject"]["m_PathID"]
            print(f"SMR {o.path_id} mesh={m_name} go={go_name.get(go_pid)} m_Quality={st.get('m_Quality')} m_UpdateWhenOffscreen={st.get('m_UpdateWhenOffscreen')}")
            # Find its Transform and walk up to root
            for tid, tr in tr_by_id.items():
                if tr["m_GameObject"]["m_PathID"] == go_pid:
                    cur = tid
                    while cur != 0:
                        t = tr_by_id[cur]
                        nm = go_name.get(t["m_GameObject"]["m_PathID"], "")
                        print(f"  Ancestor {nm}: pos={t['m_LocalPosition']} rot={t['m_LocalRotation']} scale={t['m_LocalScale']}")
                        cur = t["m_Father"]["m_PathID"]
                    break
            break
