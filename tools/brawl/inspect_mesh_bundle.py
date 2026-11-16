import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MESH_BUNDLE = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
env = UnityPy.load(str(MESH_BUNDLE))
for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt["m_Name"]
        hashes = tt.get("m_BoneNameHashes", [])
        vcount = tt["m_VertexData"]["m_VertexCount"]
        print(f"Mesh '{name}': verts={vcount}, bones={len(hashes)}, rootHash={tt.get('m_RootBoneNameHash')}")
