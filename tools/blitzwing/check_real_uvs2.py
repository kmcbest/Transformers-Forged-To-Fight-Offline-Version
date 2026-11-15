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
        vd = tt.get("m_VertexData", {})
        data = vd.get("m_DataSize")
        vcount = vd.get("m_VertexCount")
        channels = vd.get("m_Channels")
        print(f"\nMesh: {name} (vcount={vcount}, data_len={len(data)})")
        for i, ch in enumerate(channels):
            if ch['dimension'] > 0:
                print(f"  Ch {i}: stream={ch['stream']}, offset={ch['offset']}, fmt={ch['format']}, dim={ch['dimension']}")
        
        # Calculate stream strides
        # Stream 0: pos (12) + normal (12) + tangent (16) = 40
        # Stream 1: uv0 (8) = 8
        s0_size = vcount * 40
        us = []
        vs = []
        for i in range(vcount):
            u, v = struct.unpack_from("<ff", data, s0_size + i * 8)
            us.append(u)
            vs.append(v)
        print(f"  Stream 1 UV0: U=[{min(us):.4f}, {max(us):.4f}], V=[{min(vs):.4f}, {max(vs):.4f}]")
