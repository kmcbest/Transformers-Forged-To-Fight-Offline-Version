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

for obj in env.objects:
    if obj.type.name == "Avatar":
        tree = obj.read_typetree()
        print(f"Avatar: {tree.get('m_Name')}")
        tos = tree.get("m_TOS", [])
        print(f"  TOS type: {type(tos)}, len: {len(tos)}")
        if len(tos) > 0:
            print(f"  Sample TOS entry: {tos[0]}")

