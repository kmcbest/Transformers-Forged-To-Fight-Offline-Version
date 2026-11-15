import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, struct
import numpy as np

p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_blitzwing_gs_01_tank":
            submeshes = tt.get("m_SubMeshes", [])
            print("SubMeshes count:", len(submeshes))
            for i, sm in enumerate(submeshes):
                print(f"  Submesh {i}: firstByte={sm['firstByte']}, indexCount={sm['indexCount']}, topology={sm.get('topology')}")
            
            vd = tt["m_VertexData"]
            data = vd["m_DataSize"]
            vcount = vd["m_VertexCount"]
            s0_size = vcount * 40
            us = []
            vs = []
            for i in range(vcount):
                u, v = struct.unpack_from("<ff", data, s0_size + i * 8)
                us.append(u)
                vs.append(v)
            us = np.array(us)
            vs = np.array(vs)
            print(f"Total verts: {vcount}")
            print(f"Verts with V in [0, 0.5]: {np.sum((vs >= 0) & (vs <= 0.5))} (mapped to Treads)")
            print(f"Verts with V in [0.5, 1.0]: {np.sum((vs > 0.5) & (vs <= 1.0))} (mapped to Tank)")
            print(f"Verts with U > 0.5: {np.sum(us > 0.5)}")
