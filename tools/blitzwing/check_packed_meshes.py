import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(bundle_path))

for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        vc = m["m_VertexData"]["m_VertexCount"]
        b_hashes = m.get("m_BoneNameHashes", [])
        submeshes = len(m.get("m_SubMeshes", []))
        print(f"Mesh '{m.get('m_Name')}': verts={vc}, bones={len(b_hashes)}, submeshes={submeshes}")
