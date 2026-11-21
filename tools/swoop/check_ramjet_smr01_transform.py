import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import UnityPy
from scipy.spatial.transform import Rotation as R

RAMJET_BUNDLE = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(RAMJET_BUNDLE)
objs = {o.path_id: o for o in env.objects}

def get_name(pid):
    o = objs[pid]
    tt = o.read_typetree()
    if o.type.name == "Transform":
        go = objs[tt["m_GameObject"]["m_PathID"]].read_typetree()
        return go["m_Name"]
    return tt.get("m_Name", "")

for o in env.objects:
    if o.type.name == "Transform":
        tt = o.read_typetree()
        name = get_name(o.path_id)
        if name in ["ramjet_gs_deluxe2008", "Hips", "transformed", "cha_ramjet_gs_deluxe2008_01", "Reference", "COG"]:
            p_pid = tt["m_Father"]["m_PathID"]
            pname = get_name(p_pid) if p_pid in objs else "None"
            pos = tt["m_LocalPosition"]
            rot = tt["m_LocalRotation"]
            eul = R.from_quat([rot["x"], rot["y"], rot["z"], rot["w"]]).as_euler('xyz', degrees=True)
            print(f"  {name:<30} (parent={pname:<24}) pos=({pos['x']:+6.2f},{pos['y']:+6.2f},{pos['z']:+6.2f}) euler=({eul[0]:+6.1f},{eul[1]:+6.1f},{eul[2]:+6.1f})")
