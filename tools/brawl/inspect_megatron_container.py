import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "ResourceManager":
        d = obj.read()
        print("ResourceManager m_Container:")
        for k, v in d.m_Container:
            print(f"  {k} -> {v.path_id}")
    elif obj.type.name == "AssetBundle":
        d = obj.read()
        print("AssetBundle m_Container:")
        for k, v in d.m_Container:
            print(f"  {k} -> {v.asset.path_id}")
