import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}
for pid in (1469909421462177924, 3595971348910711679, 3520121911555544087):
    m = objs[pid].read_typetree()
    floats = dict(m["m_SavedProperties"]["m_Floats"])
    cols = dict(m["m_SavedProperties"]["m_Colors"])
    print(f"\nMaterial {pid} ({m['m_Name']}):")
    for k in ("_Mode", "_ZWrite", "_metallic_range", "_metallic_toggle", "_roughness_range", "_clearcoat_reflectance_range", "_emissive_range", "_emissive_none", "_emissive_overbright_range", "_emissive_ramp_range"):
        print(f"  float {k} = {floats.get(k)}")
    for k in ("_Color", "_base_col", "_emissive_intensity_col"):
        print(f"  color {k} = {cols.get(k)}")
