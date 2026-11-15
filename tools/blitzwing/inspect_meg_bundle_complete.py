import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"

env = UnityPy.load(str(bundle_path))
print(f"Total objects: {len(env.objects)}")
cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-")]
print(f"CAB: {cab_files}")

by_type = {}
for o in env.objects:
    t = o.type.name
    by_type.setdefault(t, []).append(o)

for t, objs in sorted(by_type.items()):
    print(f"Type: {t} (count={len(objs)})")
    if t in ("Mesh", "Material", "Texture2D", "AssetBundle"):
        for o in objs:
            try:
                d = o.read_typetree()
                print(f"  PID {o.path_id}: name='{d.get('m_Name')}'")
            except Exception as e:
                print(f"  PID {o.path_id}: (err: {e})")
