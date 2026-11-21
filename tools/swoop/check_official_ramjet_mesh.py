import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from pathlib import Path

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read()
        mname = data.m_Name
        pts = np.array(data.m_Vertices).reshape(-1, 3)
        print(f"\nMesh: {mname} ({len(pts)} verts)")
        print(f"  X: [{pts[:,0].min():+.3f}, {pts[:,0].max():+.3f}] span={pts[:,0].ptp():.3f}")
        print(f"  Y: [{pts[:,1].min():+.3f}, {pts[:,1].max():+.3f}] span={pts[:,1].ptp():.3f}")
        print(f"  Z: [{pts[:,2].min():+.3f}, {pts[:,2].max():+.3f}] span={pts[:,2].ptp():.3f}")
