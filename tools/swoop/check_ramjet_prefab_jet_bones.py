import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
import UnityPy
from scipy.spatial.transform import Rotation as R

RAMJET_BUNDLE = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
JET_JSON = r"e:\Agent\TFTF-blender\tools\swoop\ramjet_jet_29_authoritative_bindposes.json"

with open(JET_JSON, "r", encoding="utf-8") as f:
    jdata = json.load(f)

env = UnityPy.load(RAMJET_BUNDLE)
objs = {o.path_id: o for o in env.objects}

def get_name(pid):
    o = objs[pid]
    tt = o.read_typetree()
    if o.type.name == "Transform":
        go = objs[tt["m_GameObject"]["m_PathID"]].read_typetree()
        return go["m_Name"]
    return tt.get("m_Name", "")

def get_local_mat(tr_tt):
    pos = tr_tt["m_LocalPosition"]
    rot = tr_tt["m_LocalRotation"]
    scl = tr_tt["m_LocalScale"]
    rmat = R.from_quat([rot["x"], rot["y"], rot["z"], rot["w"]]).as_matrix()
    m = np.eye(4)
    m[:3, :3] = rmat @ np.diag([scl["x"], scl["y"], scl["z"]])
    m[:3, 3] = [pos["x"], pos["y"], pos["z"]]
    return m

# Find Reference / COG
for bname, binfo in jdata["bones"].items():
    pid = binfo["path_id"]
    tr_tt = objs[pid].read_typetree()
    # Walk up to 'transformed'
    chain = []
    cur = pid
    while cur in objs:
        cname = get_name(cur)
        ctt = objs[cur].read_typetree()
        chain.append((cname, get_local_mat(ctt)))
        if cname == "transformed":
            break
        cur = ctt["m_Father"]["m_PathID"]
    # Compute transform relative to 'transformed' (excluding 'transformed' own local transform)
    m_rel = np.eye(4)
    for cname, lmat in reversed(chain[:-1]):
        m_rel = m_rel @ lmat
    bp = binfo["bind_pose_matrix"]
    bp_mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ])
    skin_mat = m_rel @ bp_mat
    err = np.linalg.norm(skin_mat - np.eye(4))
    pos_delta = skin_mat[:3, 3]
    print(f"  {bname:<28}: err={err:8.4f} | skin_delta_pos=({pos_delta[0]:+6.3f}, {pos_delta[1]:+6.3f}, {pos_delta[2]:+6.3f})")
