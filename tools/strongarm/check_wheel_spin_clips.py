import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import UnityPy

prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)

tr_by_id, go_name = {}, {}
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
def collect(tid, parts):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    cur = parts + [nm]
    for k in range(len(cur)):
        sub = "/".join(cur[k:])
        all_crc[zlib.crc32(sub.encode("utf-8")) & 0xFFFFFFFF] = sub
    for cid in children_map.get(tid, []):
        collect(cid, cur)

for tid, tr in tr_by_id.items():
    if tr["m_Father"]["m_PathID"] == 0 and go_name.get(tr["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        collect(tid, [])

attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
print("=== Checking Wheel*_R & CenterBackCarFront in ALL Clips ===")
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if any(k in nm.lower() for k in ("vehicle", "car_", "levelup", "heavy", "special")):
            gbs = ct["m_ClipBindingConstant"]["genericBindings"]
            d = ct["m_MuscleClip"]["m_Clip"]["data"]
            s_cnt = d["m_StreamedClip"]["curveCount"]
            d_cnt = d["m_DenseClip"]["m_CurveCount"]
            cidx = 0
            animated_wheels = []
            for gb in gbs:
                p = all_crc.get(gb["path"], "")
                dim = attr_dims.get(gb["attribute"], 1)
                if ("Wheel" in p and "_R" in p) and gb["attribute"] == 2:
                    if cidx < s_cnt + d_cnt:
                        animated_wheels.append(p.split("/")[-1])
                cidx += dim
            if animated_wheels:
                print(f"  {nm:50s}: rotating Wheel_R -> {animated_wheels}")
            else:
                print(f"  {nm:50s}: NO Wheel_R rotation (const/static)")
