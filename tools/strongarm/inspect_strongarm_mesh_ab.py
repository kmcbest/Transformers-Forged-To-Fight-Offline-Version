import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\strongarm_mesh.assetbundle")
print(f"Loading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        m_name = tree.get("m_Name")
        vc = tree.get("m_VertexData", {}).get("m_VertexCount")
        sub = len(tree.get("m_SubMeshes", []))
        bp = len(tree.get("m_BindPose", []))
        bh = len(tree.get("m_BoneNameHashes", []))
        aabb = tree.get("m_LocalAABB", {})
        c = aabb.get("m_Center", {})
        e = aabb.get("m_Extent", {})
        print(f"Mesh '{m_name}': verts={vc}, submeshes={sub}, bindposes={bp}, boneHashes={bh}")
        print(f"  Center: ({c.get('x',0):.2f}, {c.get('y',0):.2f}, {c.get('z',0):.2f}) Extent: ({e.get('x',0):.2f}, {e.get('y',0):.2f}, {e.get('z',0):.2f})")
