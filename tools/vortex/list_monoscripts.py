import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle")
if not p_bundle.exists():
    p_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")

env = UnityPy.load(str(p_bundle))

scripts = {}
for obj in env.objects:
    if obj.type.name == "MonoScript":
        tree = obj.read_typetree()
        scripts[obj.path_id] = tree.get("m_ClassName", "")

print("=== MonoScripts in Grindor Bundle ===")
for pid, name in sorted(scripts.items(), key=lambda x: x[1]):
    print(f"  {pid}: {name}")

