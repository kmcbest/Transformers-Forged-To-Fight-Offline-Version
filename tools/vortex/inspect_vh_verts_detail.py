import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

ab_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle")
env = UnityPy.load(str(ab_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if "vh" in tree.get("m_Name", ""):
            print("Found mesh:", tree.get("m_Name"))
            vd = tree.get("m_VertexData", {})
            vcount = vd.get("m_VertexCount", 0)
            channels = vd.get("m_Channels", [])
            data_bytes = bytes(vd.get("m_DataSize", []))
            print(f"Vertex count: {vcount}, data bytes: {len(data_bytes)}")
            # stream 0: offset 0 is float3 pos
            # stride: offset of channel 1 is 12, ch 2 is 24, dim 4 = 16 bytes -> stream 0 stride = 40 bytes
            stride = 40
            verts = []
            for i in range(vcount):
                b = data_bytes[i*stride : i*stride + 12]
                x, y, z = np.frombuffer(b, dtype=np.float32)
                verts.append((x, y, z))
            verts = np.array(verts)
            print("Vertices shape:", verts.shape)
            print(f"X bounds: [{verts[:,0].min():.2f}, {verts[:,0].max():.2f}]")
            print(f"Y bounds: [{verts[:,1].min():.2f}, {verts[:,1].max():.2f}]")
            print(f"Z bounds: [{verts[:,2].min():.2f}, {verts[:,2].max():.2f}]")
            
            # Find rotor vertices: in vehicle space, the rotor is the highest part of the helicopter!
            # What is the highest Y in the mesh?
            max_y = verts[:,1].max()
            print(f"Max Y: {max_y:.2f}")
            # Find vertices with Y near top (e.g. Y > max_y - 0.8)
            top_verts = verts[verts[:,1] > max_y - 0.5]
            print(f"Top vertices count: {len(top_verts)}")
            top_center = top_verts.mean(axis=0)
            print(f"Top vertices center: ({top_center[0]:.4f}, {top_center[1]:.4f}, {top_center[2]:.4f})")
