import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import numpy as np
import UnityPy

RAMJET_AB = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(RAMJET_AB))

# Find SMR and Mesh for _00 and _01
objs = {o.path_id: o for o in env.objects}
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        m_pid = tt["m_Mesh"]["m_PathID"]
        if m_pid in objs:
            m_obj = objs[m_pid]
            m_tt = m_obj.read_typetree()
            name = m_tt["m_Name"]
            if "deluxe2008_00" in name or "deluxe2008_01" in name:
                print(f"\n=== SMR Mesh: {name} (verts={m_tt['m_VertexData']['m_VertexCount']}, bones={len(tt['m_Bones'])}) ===")
                # Resolve bone names
                bnames = []
                for bp in tt["m_Bones"]:
                    tr_tt = objs[bp["m_PathID"]].read_typetree()
                    go_tt = objs[tr_tt["m_GameObject"]["m_PathID"]].read_typetree()
                    bnames.append(go_tt["m_Name"])

                # Parse Stream 0 positions
                vd = m_tt["m_VertexData"]
                vc = vd["m_VertexCount"]
                buf = bytes(vd["m_DataSize"])
                chans = vd["m_Channels"]
                streams = sorted(set(c["stream"] for c in chans if c["dimension"] > 0))
                s_info = {}
                cur = 0
                for st in streams:
                    st_ch = [c for c in chans if c["dimension"] > 0 and c["stream"] == st]
                    stride = max(c["offset"] + c["dimension"] * ({0:4,1:2,2:1,3:1,6:1,10:2,11:4}.get(c["format"],4)) for c in st_ch)
                    if st == streams[-1] and vc > 0:
                        rem = len(buf) - cur
                        if rem // vc >= stride:
                            stride = rem // vc
                    s_info[st] = (cur, stride)
                    cur += ((vc * stride + 15) & ~15)
                off0, st0 = s_info[0]
                pts = np.array([struct.unpack_from("<3f", buf, off0 + i * st0) for i in range(vc)])
                print(f"  Overall Bounds (Unity XYZ): X=[{pts[:,0].min():.3f},{pts[:,0].max():.3f}], Y=[{pts[:,1].min():.3f},{pts[:,1].max():.3f}], Z=[{pts[:,2].min():.3f},{pts[:,2].max():.3f}]")

                # Parse weights
                c12, c13 = chans[12], chans[13]
                if c13["dimension"] > 0 and c13["stream"] in s_info:
                    offs, sts = s_info[c13["stream"]]
                    bone_pts = {}
                    for i in range(vc):
                        if c12["dimension"] == 4:
                            w = struct.unpack_from("<4f", buf, offs + i * sts + c12["offset"])
                            bi = struct.unpack_from("<4H" if c13["format"] == 10 else "<4I", buf, offs + i * sts + c13["offset"])
                            b0 = bi[int(np.argmax(w))]
                        else:
                            b0 = struct.unpack_from("<H" if c13["format"] == 10 else "<I", buf, offs + i * sts + c13["offset"])[0]
                        if b0 < len(bnames):
                            bone_pts.setdefault(bnames[b0], []).append(pts[i])
                    for bn in ["Head", "Neck", "Spine1", "Spine", "Hips", "LeftShoulder", "LeftShoulderPad", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftHand", "LeftHandIndex1", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "chop1_chest_center"]:
                        if bn in bone_pts:
                            arr = np.array(bone_pts[bn])
                            print(f"    Bone {bn:18s} (n={len(arr):4d}): X=[{arr[:,0].min():+.2f},{arr[:,0].max():+.2f}], Y(up)=[{arr[:,1].min():+.2f},{arr[:,1].max():+.2f}], Z(fwd)=[{arr[:,2].min():+.2f},{arr[:,2].max():+.2f}]")
