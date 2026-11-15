import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
mesh_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"

env = UnityPy.load(str(mesh_bundle))
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        print(f"\n=== Mesh: {m['m_Name']} ===")
        print(f"  Verts: {m['m_VertexData']['m_VertexCount']}")
        print(f"  Submeshes: {len(m['m_SubMeshes'])}")
        for i, sm in enumerate(m['m_SubMeshes']):
            print(f"    Submesh {i}: indexCount={sm['indexCount']}, firstVertex={sm['firstVertex']}, vertexCount={sm['vertexCount']}")
        print(f"  Bindposes: {len(m['m_BindPose'])}")
        print(f"  Bones: {len(m['m_BoneNameHashes'])}")
