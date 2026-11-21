import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("toolchain/unity_build_project/Assets/Ramjet/Bundles/ramjet_mesh.assetbundle")
if not bundle_path.exists():
    print("Bundle not found, checking Assets...")
    # search using es.exe or glob
else:
    env = UnityPy.load(str(bundle_path))
    for obj in env.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            print(f"Mesh: {tt['m_Name']}, verts: {len(tt['m_VertexData']['m_Channels'][0]) if 'm_Channels' in tt['m_VertexData'] else '?'}")
