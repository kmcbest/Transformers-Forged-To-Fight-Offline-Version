import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

print(f"=== Inspecting {Path(bundle_path).name} ===")
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        name = tree.get("m_Name")
        vc = tree.get("m_VertexData", {}).get("m_VertexCount", 0)
        submeshes = len(tree.get("m_SubMeshes", []))
        aabb = tree.get("m_LocalAABB", {})
        print(f"Mesh: {name}, verts={vc}, submeshes={submeshes}, aabb={aabb}")
