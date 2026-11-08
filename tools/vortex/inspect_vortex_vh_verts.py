import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_vortex_vh_grafted":
            print("Found cha_vortex_vh_grafted in vortex_mesh.assetbundle!")
            vdata = tree.get("m_VertexData", {})
            # Read channels
            # Read first 10 vertices
            # In UnityPy, let's unpack stream 0
            raw_bytes = vdata.get("m_DataSize")
            print(f"Vertex Count: {vdata.get('m_VertexCount')}")
            aabb = tree.get("m_LocalAABB", {})
            print("AABB:", aabb)
            break
