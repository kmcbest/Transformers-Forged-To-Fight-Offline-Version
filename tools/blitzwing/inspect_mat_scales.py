import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"e:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))

for o in env.objects:
    if o.path_id in [1722215546450231611, 8075787426780741283, 8175378592256487408]:
        mat = o.read_typetree()
        print(f"Material PID={o.path_id} name='{mat.get('m_Name')}'")
        for name, env_entry in mat.get("m_SavedProperties", {}).get("m_TexEnvs", []):
            if name in ["_base_tex", "_normal_tex", "_pbr_composite_tex"]:
                scale = env_entry.get("m_Scale")
                offset = env_entry.get("m_Offset")
                tex_pid = env_entry.get("m_Texture", {}).get("m_PathID")
                print(f"   {name}: tex_pid={tex_pid} scale={scale} offset={offset}")
