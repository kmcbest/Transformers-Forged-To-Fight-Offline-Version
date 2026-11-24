import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# Check Megatron's melee & gun audio clips so we see how Motormaster's gunshot audio fits
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
omap = {o.path_id: o for o in meg_env.objects}
print("=== Megatron ALL AudioClips ===")
for o in meg_env.objects:
    if o.type.name == "AudioClip":
        tt = o.read_typetree()
        print(f"  {o.path_id:<22} '{tt['m_Name']}' len={tt['m_Length']:.3f} res={tt['m_Resource']}")

# Check Bludgeon & Windblade PropData & RightHand positions & Windblade Sword scale vs Body
for label, bpath in [
    ("Megatron", ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"),
    ("Bludgeon", ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle"),
    ("Windblade", ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle"),
    ("Motormaster", ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle"),
]:
    e = UnityPy.load(str(bpath))
    print(f"\n=== {label} Character Scale & Props ===")
    for o in e.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_props" in tt:
                for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                    if any(w in k.lower() for w in ("sword", "gun", "mace", "cannon")):
                        print(f"  Prop '{k}': InitFlags={v.get('InitFlags')} StartActive={v.get('_startActive')} RootPath='{v.get('RootPath')}' Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} Scale={v.get('Scale')} AOC={v.get('OverrideController')}")
                break
