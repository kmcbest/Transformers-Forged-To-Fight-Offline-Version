import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import UnityPy

p = Path("toolchain/unity_build_project/AssetBundles/blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p))
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        vd = tt["m_VertexData"]
        vcount = vd["m_VertexCount"]
        data = vd["m_DataSize"]
        xs, ys, zs = [], [], []
        for i in range(vcount):
            x, y, z = struct.unpack_from("<fff", data, i * 40)
            xs.append(x)
            ys.append(y)
            zs.append(z)
        print(f"{tt['m_Name']}: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}], vcount={vcount}")
