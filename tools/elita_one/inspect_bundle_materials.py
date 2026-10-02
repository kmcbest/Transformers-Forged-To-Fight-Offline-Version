import UnityPy
from pathlib import Path

env = UnityPy.load("assets_redeco/elita_one_gs.assetbundle")
for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        print(f"Material name: {data.m_Name}")
        for p in data.m_SavedProperties.m_TexEnvs:
            print(f"  Tex property: {p[0]} -> {p[1].m_Texture.path_id}")
        for f in data.m_SavedProperties.m_Floats:
            print(f"  Float property: {f[0]} = {f[1]}")
        for c in data.m_SavedProperties.m_Colors:
            print(f"  Color property: {c[0]} = {c[1].r}, {c[1].g}, {c[1].b}, {c[1].a}")
