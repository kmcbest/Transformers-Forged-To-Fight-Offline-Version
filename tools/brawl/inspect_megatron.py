import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
print(f"Reading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name in ["GameObject", "Mesh", "Avatar", "AnimationClip"]:
        try:
            d = obj.read()
            name = getattr(d, 'name', '')
            print(f"[{obj.type.name}] PID={obj.path_id} name={name}")
        except Exception as e:
            print(f"[{obj.type.name}] PID={obj.path_id} (err: {e})")
