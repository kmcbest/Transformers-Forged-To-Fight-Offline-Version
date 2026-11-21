import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        print(f"\n==========================================")
        name = getattr(data, 'm_Name', getattr(data, 'name', 'unnamed'))
        print(f"Material name: {name} (PathID: {obj.path_id})")
        if hasattr(data, 'm_Shader') and data.m_Shader:
            try:
                shader = data.m_Shader.read()
                print(f"  Shader name: {shader.name}")
            except Exception as e:
                print(f"  Shader read error: {e}")
        props = data.m_SavedProperties
        print("  Floats:")
        for k, v in props.m_Floats:
            if any(term in k.lower() for term in ["emiss", "over", "metal", "rough", "light", "glow"]):
                print(f"    {k} = {v}")
        print("  Colors:")
        for k, v in props.m_Colors:
            print(f"    {k} = (r={v.r:.3f}, g={v.g:.3f}, b={v.b:.3f}, a={v.a:.3f})")
        print("  Textures:")
        for k, v in props.m_TexEnvs:
            try:
                tex_name = getattr(v.m_Texture.read(), 'm_Name', 'unknown') if v.m_Texture else "None"
            except Exception:
                tex_name = "RefNotFound"
            print(f"    {k} = {tex_name}")
