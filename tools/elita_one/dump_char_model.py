import UnityPy
from pathlib import Path

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name == "character_model":
            print("Found character_model children:")
            for comp in data.m_Components:
                cdata = comp.read()
                if hasattr(cdata, 'm_Children'):
                    for child_ref in cdata.m_Children:
                        child_tr = child_ref.read()
                        child_go = child_tr.m_GameObject.read()
                        cname = getattr(child_go, 'name', getattr(child_go, 'm_Name', ''))
                        print(f"  - {cname}")
