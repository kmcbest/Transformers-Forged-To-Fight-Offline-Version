import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\jetfire_gs_leader2014_odr\jetfire_gs_leader2014.assetbundle"
env_j = UnityPy.load(donor_path)

out_obj = Path(r"E:\Agent\TFTF-blender\scratch\jetfire_rifle.obj")
out_obj.parent.mkdir(parents=True, exist_ok=True)

for obj in env_j.objects:
    if obj.path_id == -4439679313609908059:
        mesh = obj.read()
        # Export as obj using UnityPy's export or parse
        with open(out_obj, "w", encoding="utf-8") as f:
            f.write(mesh.export())
        print(f"Dumped Jetfire rifle OBJ to {out_obj} ({out_obj.stat().st_size} bytes)")
