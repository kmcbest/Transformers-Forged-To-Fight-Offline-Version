import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            print("Found cha_grindor_cin_rotf_01!")
            aabb = tree.get("m_LocalAABB", {})
            print("LocalAABB:", aabb)
            
            # Read vertex stream 0
            vdata = tree.get("m_VertexData", {})
            streams = vdata.get("m_Streams", [])
            data_bytes = vdata.get("m_DataSize")
            # Let's inspect channels
            channels = vdata.get("m_Channels", [])
            for i, ch in enumerate(channels):
                print(f"Channel {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")

            # Also let's inspect the bindposes array
            bp = tree.get("m_BindPose", [])
            print(f"Total bindposes: {len(bp)}")
            # Print first 3 bindpose matrices
            for b_idx in range(min(3, len(bp))):
                mat = bp[b_idx]
                m_arr = np.array([
                    [mat['e00'], mat['e01'], mat['e02'], mat['e03']],
                    [mat['e10'], mat['e11'], mat['e12'], mat['e13']],
                    [mat['e20'], mat['e21'], mat['e22'], mat['e23']],
                    [mat['e30'], mat['e31'], mat['e32'], mat['e33']]
                ])
                print(f"BindPose[{b_idx}]:\n{m_arr}")
            break
