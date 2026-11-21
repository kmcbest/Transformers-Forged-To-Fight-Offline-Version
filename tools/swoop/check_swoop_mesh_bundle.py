import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mesh_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\swoop_mesh.assetbundle")
env = UnityPy.load(str(mesh_bundle))

for obj in env.objects:
    try:
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        print(f"[{obj.type.name}] {name} (PID: {obj.path_id})")
    except:
        print(f"[{obj.type.name}] (PID: {obj.path_id})")
