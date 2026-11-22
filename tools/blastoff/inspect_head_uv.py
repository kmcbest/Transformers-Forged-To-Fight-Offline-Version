import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MESH_BUNDLE = Path("toolchain/unity_build_project/AssetBundles/blastoff_mesh.assetbundle")
env = UnityPy.load(str(MESH_BUNDLE))
mesh_obj = next(o for o in env.objects if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_blastoff_gs_00")
tt = mesh_obj.read_typetree()

# Let's inspect submesh index or vertices at high Y (> 10.5)
# In Unity typetree, vertex data is in m_VertexData
print("m_VertexData keys:", tt["m_VertexData"].keys())
# Let's check submeshes
print("Submeshes count:", len(tt["m_SubMeshes"]))
for i, sm in enumerate(tt["m_SubMeshes"]):
    print(f"Submesh {i}: firstVertex={sm.get('firstVertex')}, vertexCount={sm.get('vertexCount')}, indexCount={sm.get('indexCount')}")
