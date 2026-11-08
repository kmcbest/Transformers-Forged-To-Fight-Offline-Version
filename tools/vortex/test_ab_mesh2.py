import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ab_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle")
env = UnityPy.load(str(ab_path))
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        print(f"Mesh: {tree.get('m_Name')}")
        aabb = tree.get("m_LocalAABB", {})
        print(f"  Center: {aabb.get('m_Center')}")
        print(f"  Extent: {aabb.get('m_Extent')}")

