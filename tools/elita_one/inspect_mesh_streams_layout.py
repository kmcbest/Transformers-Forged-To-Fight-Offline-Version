import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
env = UnityPy.load(str(elita_bundle))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_elita_one_gs_00":
            vdata = tree.get("m_VertexData", {})
            print("m_Streams:", vdata.get("m_Streams"))
            print("Vertex count:", vdata.get("m_VertexCount"))
            print("DataSize length:", len(vdata.get("m_DataSize", b"")))
