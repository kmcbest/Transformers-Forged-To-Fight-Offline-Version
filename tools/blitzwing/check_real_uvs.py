import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, struct

p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        name = tt["m_Name"]
        if "tank" in name or "jet" in name:
            vcount = tt["m_VertexData"]["m_VertexCount"]
            data = bytes(tt["m_VertexData"]["m_DataSize"])
            stream1_start = vcount * 40
            us, vs = [], []
            for i in range(vcount):
                u, v = struct.unpack_from("<ff", data, stream1_start + i * 8)
                us.append(u); vs.append(v)
            print(f"{name} UV0 range:")
            print(f"  U: [{min(us):.4f}, {max(us):.4f}]")
            print(f"  V: [{min(vs):.4f}, {max(vs):.4f}]")
