import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

for name, path in [
    ("StarSaber (White bot)", Path(r"E:\Agent\TFTF-blender\assets_redeco\starsaber_gs_leader2014.assetbundle")),
    ("Lifeline (White/Teal bot)", Path(r"E:\Agent\TFTF-blender\assets_redeco\lifeline_gs_deluxe2014.assetbundle")),
    ("Prowl (White bot)", Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")),
    ("ElitaOne", Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")),
]:
    if not path.exists():
        continue
    print(f"\n=== {name} ===")
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type.name == "Material":
            m = obj.read_typetree()
            mn = m.get("m_Name", "")
            if not mn.startswith("fx_") and not mn.startswith("Shadow"):
                props = m.get("m_SavedProperties", {})
                fl = {k: round(v, 3) for k, v in props.get("m_Floats", []) if k in ("_Mode", "_metallic_range", "_roughness_range", "_emissive_range", "_emissive_overbright_range", "_reflectance", "_clearcoat_reflectance_range")}
                co = {k: (round(v['r'],3), round(v['g'],3), round(v['b'],3)) for k, v in props.get("m_Colors", []) if k in ("_Color", "_base_col", "_emissive_intensity_col")}
                print(f"  Mat '{mn}': {fl} | {co}")
