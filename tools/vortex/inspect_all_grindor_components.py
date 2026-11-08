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

print("=== All Types in Grindor Bundle ===")
type_counts = {}
for obj in env.objects:
    t = obj.type.name
    type_counts[t] = type_counts.get(t, 0) + 1

for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t:30s}: {c}")

print("\n=== All MonoBehaviours in Grindor Bundle ===")
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        ms_id = tree.get("m_Script", {}).get("m_PathID")
        print(f"MonoBehaviour at path_id {obj.path_id}: go_id={go_id}, script_id={ms_id}")

