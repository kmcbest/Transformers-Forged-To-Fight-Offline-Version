import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

OUT_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(OUT_BUNDLE))

MAT_VEHICLE_PID = 1722215546450231611
for o in env.objects:
    if o.path_id == MAT_VEHICLE_PID:
        tt = o.read_typetree()
        envs = tt["m_SavedProperties"]["m_TexEnvs"]
        print(f"Material {MAT_VEHICLE_PID} ({tt['m_Name']}) textures:")
        for name, prop in envs:
            if name in ("_base_tex", "_normal_tex", "_pbr_composite_tex"):
                print(f"  {name}: {prop['m_Texture']['m_PathID']}")
