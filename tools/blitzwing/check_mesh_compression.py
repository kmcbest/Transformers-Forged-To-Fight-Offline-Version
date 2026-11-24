import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

mb = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
e = UnityPy.load(str(mb))
for o in e.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"\n=== {tt['m_Name']} ===")
        print("  m_VertexData keys:", {k: (len(v) if isinstance(v, (bytes, bytearray, list)) else v) for k, v in tt["m_VertexData"].items()})
        print("  m_CompressedMesh:", {k: v.get("m_NumItems") if isinstance(v, dict) else v for k, v in tt["m_CompressedMesh"].items()})
        print("  m_IsReadable:", tt.get("m_IsReadable"), "m_MeshCompression:", tt.get("m_MeshCompression"))
