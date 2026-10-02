import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if not name.startswith("fx_"):
            print(f"Material: {name}")
            if hasattr(data, 'm_SavedProperties'):
                tex_envs = data.m_SavedProperties.m_TexEnvs
                for tex_prop, tex_info in tex_envs:
                    if tex_info.m_Texture:
                        try:
                            tex_obj = tex_info.m_Texture.read()
                            tname = getattr(tex_obj, 'name', getattr(tex_obj, 'm_Name', ''))
                            print(f"  {tex_prop}: {tname}")
                        except Exception as e:
                            print(f"  {tex_prop}: [external CAB]")
