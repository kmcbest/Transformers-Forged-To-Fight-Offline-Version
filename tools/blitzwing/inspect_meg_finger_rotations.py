import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from pathlib import Path
import UnityPy

DONOR = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(DONOR))

m00 = next(o for o in env.objects if o.path_id == 3463271531423751283).read_typetree()
bps = m00["m_BindPose"]
hashes = m00["m_BoneNameHashes"]

# Find LeftHandIndex1
avatar = next(o for o in env.objects if o.type.name == "Avatar" and "00" in o.read_typetree().get("m_Name", "")).read_typetree()
tos_map = {k: v for k, v in avatar.get("m_TOS", [])}

for idx, h in enumerate(hashes):
    bpath = tos_map.get(h, str(h))
    bname = bpath.split("/")[-1]
    if "index" in bname.lower() or "thumb" in bname.lower():
        bp = bps[idx]
        mat = np.array([
            [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
            [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
            [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
            [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
        ])
        inv = np.linalg.inv(mat)
        print(f"Bone [{idx}] {bname}:")
        print("  World Rest Translation:", np.round(inv[:3, 3], 3))
        print("  World Rest Rotation (3x3):")
        print(np.round(inv[:3, :3], 3))
