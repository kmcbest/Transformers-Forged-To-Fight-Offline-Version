import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
out_obj = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_ref.obj")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        name = getattr(mesh, 'm_Name', '')
        if "00" in name and not "wpns" in name:
            print(f"Exporting Prowl reference mesh: {name}")
            # In UnityPy, mesh.export() can export directly to obj
            with open(out_obj, "w", encoding="utf-8") as f:
                f.write(mesh.export())
            print(f"Saved {out_obj}")
            break
