import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import UnityPy

# Let's see what happens if we directly transform the vertex data of cha_blitzwing_gs_01_tank
p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_blitzwing_gs_01_tank":
            vd = tt["m_VertexData"]
            data = bytearray(vd["m_DataSize"])
            vcount = vd["m_VertexCount"]
            stride = 40
            
            # Read existing
            xs, ys, zs = [], [], []
            for i in range(vcount):
                x, y, z = struct.unpack_from("<fff", data, i * stride)
                xs.append(x); ys.append(y); zs.append(z)
            
            print("Original Tank bounds:")
            print(f"  X: [{min(xs):.3f}, {max(xs):.3f}]")
            print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}]")
            print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}]")
            
            # Transformed: x_new = x, y_new = z - 1.549, z_new = -y
            new_xs = [x for x in xs]
            new_ys = [z - 1.549 for z in zs]
            new_zs = [-y for y in ys]
            print("\nTransformed Tank bounds:")
            print(f"  X: [{min(new_xs):.3f}, {max(new_xs):.3f}]")
            print(f"  Y: [{min(new_ys):.3f}, {max(new_ys):.3f}]")
            print(f"  Z: [{min(new_zs):.3f}, {max(new_zs):.3f}]")
