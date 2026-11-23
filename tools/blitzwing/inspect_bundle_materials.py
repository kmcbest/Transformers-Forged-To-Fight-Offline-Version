import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"e:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
if not bundle_path.exists():
    print(f"Error: {bundle_path} does not exist")
    sys.exit(1)

env = UnityPy.load(str(bundle_path))

print(f"Loaded {bundle_path.name}")
for o in env.objects:
    if o.type.name == "Material":
        mat = o.read_typetree()
        name = mat.get("m_Name", "")
        tex_envs = mat.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        tex_map = {k: v.get("m_Texture", {}).get("m_PathID") for k, v in tex_envs}
        print(f"Material PID={o.path_id} name='{name}':")
        for k in ["_base_tex", "_normal_tex", "_pbr_composite_tex"]:
            print(f"   {k}: {tex_map.get(k)}")

print("\nTextures in bundle:")
for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        print(f"Texture PID={o.path_id} name='{t.m_Name}' {t.m_Width}x{t.m_Height}")
