import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if "jet" in tt["m_Name"]:
            vd = tt["m_VertexData"]
            vcount = vd["m_VertexCount"]
            size = len(vd["m_DataSize"])
            print(f"Jet Mesh in blitzwing_mesh: verts={vcount}, DataSize={size}, bytes_per_vert={size/vcount}")
            for i, ch in enumerate(vd["m_Channels"]):
                if ch["dimension"] > 0:
                    print(f"  ch[{i}]: {ch}")
