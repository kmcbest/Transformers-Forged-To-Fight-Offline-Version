import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Avatar":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        print(f"Avatar: '{name}'")
        if hasattr(data, 'm_Avatar'):
            m_av = data.m_Avatar
            print(f"  m_Avatar: is_human={m_av.m_IsHuman}")
