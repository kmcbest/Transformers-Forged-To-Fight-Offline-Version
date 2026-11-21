import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

scripts = {}
for obj in env.objects:
    if obj.type.name == "MonoScript":
        d = obj.read_typetree()
        cname = d.get("m_ClassName", "")
        scripts[cname] = obj.path_id

for target in ["Projectile", "MoveSet", "PrefabLib", "MoveSequencer"]:
    if target in scripts:
        print(f"Ramjet has {target}: PID = {scripts[target]}")
    else:
        print(f"Ramjet MISSING {target}!")
