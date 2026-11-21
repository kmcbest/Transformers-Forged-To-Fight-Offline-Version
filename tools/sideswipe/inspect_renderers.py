import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name in ["SkinnedMeshRenderer", "MeshRenderer"]:
        data = obj.read()
        print(f"\nRenderer: {getattr(data, 'm_Name', getattr(data, 'name', 'unnamed'))} (Type: {obj.type.name}, PathID: {obj.path_id})")
        if hasattr(data, 'm_Materials'):
            for i, mat_ptr in enumerate(data.m_Materials):
                if mat_ptr:
                    try:
                        mat = mat_ptr.read()
                        print(f"  Material[{i}]: {getattr(mat, 'm_Name', 'unnamed')} (PathID: {mat_ptr.path_id})")
                    except Exception as e:
                        print(f"  Material[{i}]: PathID {mat_ptr.path_id} (read err: {e})")
                else:
                    print(f"  Material[{i}]: None")
