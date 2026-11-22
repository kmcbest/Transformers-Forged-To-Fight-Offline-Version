import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
for bname in ["blastoff_gs.assetbundle", "brawl_gs.assetbundle", "onslaught_gs.assetbundle", "vortex_gs.assetbundle", "swindle_gs.assetbundle"]:
    bp = ROOT / "assets_redeco" / bname
    if not bp.exists():
        continue
    print(f"\n================ {bname} ================")
    env = UnityPy.load(str(bp))
    obj_map = {o.path_id: o for o in env.objects}
    for o in env.objects:
        if o.type.name == "Material":
            tt = o.read_typetree()
            mname = tt.get("m_Name", "")
            if mname.startswith("fx_"):
                continue
            sp = tt.get("m_SavedProperties", {})
            floats = dict(sp.get("m_Floats", []))
            cols = dict(sp.get("m_Colors", []))
            if "_pbr_composite_tex" in dict(sp.get("m_TexEnvs", [])):
                tex_envs = dict(sp.get("m_TexEnvs", []))
                em_col = cols.get("_emissive_intensity_col")
                if not em_col or (em_col.get("r",0)==0 and em_col.get("g",0)==0 and em_col.get("b",0)==0):
                    continue
                print(f"  Mat '{mname[:20]}' PID={o.path_id}: keywords={tt.get('m_ShaderKeywords')}")
                print(f"    ob={floats.get('_emissive_overbright_range')}, er={floats.get('_emissive_range')}, ramp={floats.get('_emissive_ramp_range')}, pulse={floats.get('_emissive_pulse_intensity_range')}, em_col={em_col}")
                for tprop in ["_base_tex", "_normal_tex", "_pbr_composite_tex", "_emissive_tex"]:
                    tp = tex_envs.get(tprop, {}).get("m_Texture", {}).get("m_PathID", 0)
                    if tp in obj_map:
                        t = obj_map[tp].read()
                        arr = np.array(t.image)
                        sc = tex_envs[tprop].get("m_Scale")
                        of = tex_envs[tprop].get("m_Offset")
                        print(f"    {tprop:18s}: '{t.m_Name}' {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat} cs={getattr(t,'m_ColorSpace', '?')} scale={sc} off={of}")
                        if tprop == "_pbr_composite_tex" and arr.ndim == 3 and arr.shape[2] >= 3:
                            em = arr[:, :, 2]
                            print(f"      RAOE.B (>20 pct={(em>20).mean()*100:.2f}%, max={em.max()}, >200 pct={(em>200).mean()*100:.2f}%)")
