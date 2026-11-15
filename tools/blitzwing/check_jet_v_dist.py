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
        if "jet" in tt["m_Name"]:
            vcount = tt["m_VertexData"]["m_VertexCount"]
            data = bytes(tt["m_VertexData"]["m_DataSize"])
            stream1_start = vcount * 40
            neg_v = 0
            pos_v = 0
            for i in range(vcount):
                u, v = struct.unpack_from("<ff", data, stream1_start + i * 8)
                if v < 0:
                    neg_v += 1
                else:
                    pos_v += 1
            print(f"Jet UVs: {neg_v} negative V, {pos_v} positive V out of {vcount} total")
