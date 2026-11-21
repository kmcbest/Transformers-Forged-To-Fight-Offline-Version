import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mm_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\motormaster_gs_voyager2015_odr\motormaster_gs_voyager2015.assetbundle"
env_m = UnityPy.load(mm_path)

out_obj = Path(r"E:\Agent\TFTF-blender\scratch\motormaster_rifle.obj")
out_obj.parent.mkdir(parents=True, exist_ok=True)

for obj in env_m.objects:
    if obj.path_id == 2697988736999805448:
        mesh = obj.read()
        with open(out_obj, "w", encoding="utf-8") as f:
            f.write(mesh.export())
        print(f"Dumped Motormaster rifle OBJ to {out_obj} ({out_obj.stat().st_size} bytes)")
