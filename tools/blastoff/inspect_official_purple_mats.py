import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundles = [
    ROOT / "assets_redeco/brawl_gs.assetbundle",
    ROOT / "assets_redeco/onslaught_gs.assetbundle",
    ROOT / "assets_redeco/vortex_gs.assetbundle",
    ROOT / "assets_redeco/swindle_gs.assetbundle",
    ROOT / "assets_redeco/tarn_gs.assetbundle",
]

for bp in bundles:
    if not bp.exists():
        continue
    print(f"\n=== {bp.name} ===")
    env = UnityPy.load(str(bp))
    for o in env.objects:
        if o.type.name == "Material":
            tt = o.read_typetree()
            mname = tt.get("m_Name", "")
            if mname.startswith("fx_"):
                continue
            sp = tt.get("m_SavedProperties", {})
            floats = dict(sp.get("m_Floats", []))
            cols = dict(sp.get("m_Colors", []))
            if "_emissive_intensity_col" in cols:
                print(f"  Mat {mname[:24]:24s}: ob={floats.get('_emissive_overbright_range')}, er={floats.get('_emissive_range')}, ramp={floats.get('_emissive_ramp_range')}, scaler={floats.get('_emission_scaler')}")
                print(f"    em_col={cols.get('_emissive_intensity_col')}")
                print(f"    _Color={cols.get('_Color')}, _base_col={cols.get('_base_col')}")
