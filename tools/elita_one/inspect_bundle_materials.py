import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
for obj in env.objects:
    if obj.type.name == "Material":
        mat = obj.read_typetree()
        print(f"Material: {mat.get('m_Name')}, path_id={obj.path_id}")
        print(f"  m_Shader: {mat.get('m_Shader')}")
        for t in mat.get('m_SavedProperties', {}).get('m_TexEnvs', []):
            print(f"  Tex: {t[0]} -> {t[1].get('m_Texture')}")
        for f in mat.get('m_SavedProperties', {}).get('m_Floats', []):
            if 'emissive' in f[0].lower():
                print(f"  Float: {f}")
        for c in mat.get('m_SavedProperties', {}).get('m_Colors', []):
            if 'emissive' in c[0].lower():
                print(f"  Color: {c}")
