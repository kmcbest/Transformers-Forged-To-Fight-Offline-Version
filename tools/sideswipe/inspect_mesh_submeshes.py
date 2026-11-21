import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\sideswipe_mesh.assetbundle")
env = UnityPy.load(str(p))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"Mesh: {tt['m_Name']}")
        print(f"  SubMeshes count: {len(tt['m_SubMeshes'])}")
        for i, sm in enumerate(tt['m_SubMeshes']):
            print(f"    SubMesh[{i}]: firstByte={sm['firstByte']}, indexCount={sm['indexCount']}, topology={sm.get('topology')}")
