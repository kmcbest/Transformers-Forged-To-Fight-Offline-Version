import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name in ["cha_arcee_gs_deluxe2014_00", "cha_arcee_gs_deluxe2014_01"]:
            print(f"GameObject: {name}")
            for comp in data.m_Components:
                cdata = comp.read()
                if type(cdata).__name__ == "SkinnedMeshRenderer":
                    print(f"  Materials on {name}:")
                    for m in cdata.m_Materials:
                        m_obj = m.read()
                        m_name = getattr(m_obj, 'name', getattr(m_obj, 'm_Name', ''))
                        print(f"    - {m_name}")
