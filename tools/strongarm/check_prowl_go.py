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
        if "01" in name or "transformed" in name.lower() or name == "cha_prowl_gs_deluxe2016":
            print(f"GameObject: {name} (PathID: {obj.path_id})")
            for comp in getattr(data, 'm_Components', []):
                c = comp.read()
                print(f"  Component: {type(c).__name__}")
