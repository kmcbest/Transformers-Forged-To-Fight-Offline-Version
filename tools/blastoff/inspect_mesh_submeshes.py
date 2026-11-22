import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mb_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle")
env = UnityPy.load(str(mb_path))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        submeshes = tt.get("m_SubMeshes", [])
        print(f"Mesh '{tt['m_Name']}' submesh count = {len(submeshes)}")
        for idx, sm in enumerate(submeshes):
            print(f"   Submesh[{idx}]: firstByte={sm.get('firstByte')}, indexCount={sm.get('indexCount')}, topology={sm.get('topology')}")
