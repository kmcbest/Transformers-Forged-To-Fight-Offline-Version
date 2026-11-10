import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'm_Name', getattr(data, 'name', ''))
        if any(k in name.lower() for k in ["prowl", "deluxe", "smr", "_00", "_01", "mesh", "cha"]):
            print(f"GameObject: {name}")
