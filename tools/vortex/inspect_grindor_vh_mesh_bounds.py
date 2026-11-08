import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            vd = tree.get("m_VertexData", {})
            vcount = vd.get("m_VertexCount", 0)
            data_bytes = bytes(vd.get("m_DataSize", []))
            stride = 40  # channel 0 float3, ch 1 float3, ch 2 float4 = 40 bytes
            verts = []
            for i in range(vcount):
                b = data_bytes[i*stride : i*stride + 12]
                verts.append(np.frombuffer(b, dtype=np.float32))
            verts = np.array(verts)
            print("Grindor Original Vehicle Mesh Bounds:")
            print(f"  X: [{verts[:,0].min():.2f}, {verts[:,0].max():.2f}] (span={verts[:,0].max()-verts[:,0].min():.2f})")
            print(f"  Y: [{verts[:,1].min():.2f}, {verts[:,1].max():.2f}] (span={verts[:,1].max()-verts[:,1].min():.2f})")
            print(f"  Z: [{verts[:,2].min():.2f}, {verts[:,2].max():.2f}] (span={verts[:,2].max()-verts[:,2].min():.2f})")
            print(f"  Center: {verts.mean(axis=0)}")
            
            # Find Grindor rotor vertices (highest Y)
            high_y = verts[verts[:,1] > verts[:,1].max() - 0.5]
            print(f"Grindor top rotor verts: {len(high_y)}, center: {high_y.mean(axis=0)}")
