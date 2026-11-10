import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zlib
import UnityPy

# Check prowl_anims_registered.assetbundle where tactical_normal_idle lives!
bpath = r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"
env = UnityPy.load(bpath)
prowl_b = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_b)

# Build crc map from Official Prowl
tr_by_id, go_name = {}, {}
for o in env_p.objects:
    if o.type.name == "GameObject":
        go_name[o.path_id] = o.read_typetree().get("m_Name", "")
    elif o.type.name == "Transform":
        tr_by_id[o.path_id] = o.read_typetree()

children = {}
for tid, tr in tr_by_id.items():
    for c in tr["m_Children"]:
        children.setdefault(tid, []).append(c["m_PathID"])

all_crc = {}
def collect(tid, parts):
    nm = go_name.get(tr_by_id[tid]["m_GameObject"]["m_PathID"], "")
    cur = parts + [nm]
    for k in range(len(cur)):
        sub = "/".join(cur[k:])
        all_crc[zlib.crc32(sub.encode("utf-8")) & 0xFFFFFFFF] = sub
    for cid in children.get(tid, []):
        collect(cid, cur)

for tid, tr in tr_by_id.items():
    if tr["m_Father"]["m_PathID"] == 0 and go_name.get(tr["m_GameObject"]["m_PathID"]) == "Prowl_GS_Deluxe2016":
        collect(tid, [])

attr_dims = {1: 3, 2: 4, 3: 3, 4: 3}
for ev_name, ev in [("prowl_anims_registered", env), ("prowl_official", env_p)]:
    for o in ev.objects:
        if o.type.name == "AnimationClip":
            ct = o.read_typetree()
            nm = ct.get("m_Name", "")
            if nm in ("tactical_normal_idle", "frontend_Prowl_levelup_idle", "tactical_normal_attacklight_01_jab_L", "Prowl_Normal_attackSpecial_01"):
                print(f"\n=== [{ev_name}] Clip: {nm} ===")
                gbs = ct["m_ClipBindingConstant"]["genericBindings"]
                d = ct["m_MuscleClip"]["m_Clip"]["data"]
                const_arr = d["m_ConstantClip"]["data"]
                dense = d["m_DenseClip"]
                s_cnt = d["m_StreamedClip"]["curveCount"]
                d_cnt = dense["m_CurveCount"]
                d_arr = dense["m_SampleArray"]
                cidx = 0
                for gb in gbs:
                    p = all_crc.get(gb["path"], f"CRC:{gb['path']}")
                    attr = gb["attribute"]
                    dim = attr_dims.get(attr, 1)
                    if attr == 2 and any(k in p for k in ("LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "Index", "Middle", "Thumb")):
                        if cidx < s_cnt:
                            src = "STREAM"
                        elif cidx < s_cnt + d_cnt:
                            di = cidx - s_cnt
                            src = f"DENSE f0={[round(d_arr[di+k],3) for k in range(dim)]}"
                        else:
                            ci = cidx - (s_cnt + d_cnt)
                            src = f"CONST {[round(x,3) for x in const_arr[ci:ci+dim]]}"
                        print(f"  {p:45s} -> {src}")
                    cidx += dim
