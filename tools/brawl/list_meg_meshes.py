import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\assets_base\characters\cha_megatron_cin_rotf.assetbundle"
if not Path(bundle_path).exists():
    print(f"File not found: {bundle_path}")
    sys.exit(0)

env = UnityPy.load(bundle_path)
for obj in env.objects:
    if obj.type.name == "Mesh":
        d = obj.read()
        print(f"Mesh name: {d.name}")
