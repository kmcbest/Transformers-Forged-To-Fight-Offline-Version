import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import UnityPy

p = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        vd = tt.get("m_VertexData")
        if not vd or "m_DataSize" not in vd:
            continue
        data = bytes(vd["m_DataSize"])
        vcount = vd["m_VertexCount"]
        stride = 40
        xs, ys, zs = [], [], []
        for i in range(vcount):
            off = i * stride
            x, y, z = struct.unpack_from("<fff", data, off)
            xs.append(x)
            ys.append(y)
            zs.append(z)
        print(f"Mesh: '{tt['m_Name']}' (verts={vcount}, bones={len(tt.get('m_BoneNameHashes', []))}, bindposes={len(tt.get('m_BindPose', []))})")
        print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] center={(min(xs)+max(xs))/2:.3f}")
        print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] center={(min(ys)+max(ys))/2:.3f}")
        print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] center={(min(zs)+max(zs))/2:.3f}")
