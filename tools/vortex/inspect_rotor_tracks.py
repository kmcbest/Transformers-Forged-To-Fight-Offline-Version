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

# RotorMain hash in TOS_01: 3459633487
# RotorMainBlade1: 2982884341
# RotorMainBlade2: 683827791
# RotorMainBlade3: 1606767321
# RotorMainBlade4: 3248605050

target_hashes = {
    3459633487: "RotorMain",
    2982884341: "RotorMainBlade1",
    683827791:  "RotorMainBlade2",
    1606767321: "RotorMainBlade3",
    3248605050: "RotorMainBlade4",
}

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        c_name = tree.get("m_Name", "")
        if c_name == "frontend_Grindor_levelup_vehicle_idle_transformed":
            print(f"Clip: {c_name}")
            bindings = tree.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            for idx, b in enumerate(bindings):
                p = b.get("path")
                if p in target_hashes:
                    print(f"Binding {idx}: path={target_hashes[p]} ({p}), attr={b.get('attribute')}, typeID={b.get('typeID')}")

