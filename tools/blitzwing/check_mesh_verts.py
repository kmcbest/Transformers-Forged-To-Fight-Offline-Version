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
        m = o.read()
        print(f"Mesh '{m.m_Name}': verts={len(m.m_Vertices) if hasattr(m, 'm_Vertices') else 'N/A'}")
        tt = o.read_typetree()
        c_verts = tt.get("m_CompressedMesh", {}).get("m_Vertices", {}).get("m_NumItems", 0)
        print(f"  CompressedMesh numItems: {c_verts}")
