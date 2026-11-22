import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np

bp = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\necrotronus_gs_kabam_odr\necrotronus_gs_kabam.assetbundle")
env = UnityPy.load(str(bp))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        sp = tt.get("m_SavedProperties", {})
        floats = dict(sp.get("m_Floats", []))
        cols = dict(sp.get("m_Colors", []))
        texs = dict(sp.get("m_TexEnvs", []))
        em = cols.get("_emissive_intensity_col")
        if em and em.get("b", 0) > em.get("r", 0):
            print(f"Mat '{tt.get('m_Name')}' PID={o.path_id}: ob={floats.get('_emissive_overbright_range')}, er={floats.get('_emissive_range')}, ramp={floats.get('_emissive_ramp_range')}, pulse={floats.get('_emissive_pulse_intensity_range')}")
            print(f"  _emissive_intensity_col = {em}")
            print(f"  _Color = {cols.get('_Color')}, _base_col = {cols.get('_base_col')}")
            for tp in ("_base_tex", "_pbr_composite_tex"):
                pid = texs.get(tp, {}).get("m_Texture", {}).get("m_PathID", 0)
                if pid in obj_map:
                    t = obj_map[pid].read()
                    arr = np.array(t.image)
                    print(f"  {tp}: '{t.m_Name}' {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat} shape={arr.shape}")
                    if tp == "_pbr_composite_tex" and arr.ndim == 3:
                        b = arr[:, :, 2]
                        nz = b[b > 20]
                        if len(nz) > 0:
                            print(f"    RAOE.B (>20): pct={len(nz)/b.size*100:.2f}%, p50={np.percentile(nz,50):.0f}, p90={np.percentile(nz,90):.0f}, max={nz.max()}")
