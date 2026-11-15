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
        if tt["m_Name"] == "cha_blitzwing_gs_01_tank":
            print("Channels:")
            for i, ch in enumerate(tt["m_VertexData"]["m_Channels"]):
                print(f"  ch[{i}]: {ch}")
            print("Streams:")
            for i, st in enumerate(tt["m_VertexData"].get("m_Streams", [])):
                print(f"  st[{i}]: {st}")
