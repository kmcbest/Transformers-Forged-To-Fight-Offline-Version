import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

for pid in [-3660570848581127988, 2297153707519481197, -3815473324432562333, 4113389322536752908]:
    obj = obj_map.get(pid)
    if obj:
        print(f"MonoScript {pid}: {obj.read_typetree().get('m_Name', '')} (class_name: {obj.read_typetree().get('m_ClassName', '')})")
    else:
        print(f"MonoScript {pid}: not found in local bundle")
