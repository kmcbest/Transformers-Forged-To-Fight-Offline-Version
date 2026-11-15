import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
mesh_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"
print("Mesh bundle exists:", mesh_bundle.exists())

env = UnityPy.load(str(mesh_bundle))
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        print(f"Mesh: name='{m['m_Name']}', verts={m['m_VertexData']['m_VertexCount']}, submeshes={len(m['m_SubMeshes'])}, bindposes={len(m['m_BindPose'])}, bones={len(m['m_BoneNameHashes'])}")
