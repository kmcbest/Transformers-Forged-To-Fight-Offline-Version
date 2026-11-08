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
            vd = tree.get("m_VertexData", {})
            vcount = vd.get("m_VertexCount", 0)
            data_bytes = bytes(vd.get("m_DataSize", []))
            stride = 40
            verts = []
            for i in range(vcount):
                b = data_bytes[i*stride : i*stride + 12]
                verts.append(np.frombuffer(b, dtype=np.float32))
            verts = np.array(verts)
            
            # Find vertices with large horizontal span (the rotor blades span ~14m from x=-7 to x=+7)
            # In vehicle space:
            # Rotor blades have span in X and Z!
            # What vertices have Y > 4.5?
            high_y_verts = verts[verts[:,1] > 4.5]
            print(f"Verts with Y > 4.5: {len(high_y_verts)}")
            print(f"X bounds of high Y: [{high_y_verts[:,0].min():.2f}, {high_y_verts[:,0].max():.2f}]")
            print(f"Z bounds of high Y: [{high_y_verts[:,2].min():.2f}, {high_y_verts[:,2].max():.2f}]")
            print(f"Center of high Y: {high_y_verts.mean(axis=0)}")
