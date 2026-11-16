import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        d = obj.read()
        name = getattr(d, 'm_Name', '')
        if "01" in name:
            # Export obj
            out_obj = Path(r"E:\Agent\TFTF-blender\tools\brawl\meg_veh_rest.obj")
            # In UnityPy, export obj
            with open(out_obj, "w") as f:
                f.write(d.export())
            print(f"Exported {name} to {out_obj}")
            break
