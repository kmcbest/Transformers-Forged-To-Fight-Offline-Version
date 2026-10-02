import UnityPy
from pathlib import Path

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name == "Arcee_GS_Deluxe2014":
            print(f"Found root GameObject: {name}")
            def print_tree(go_data, indent=0, max_depth=3):
                if indent > max_depth: return
                gname = getattr(go_data, 'name', getattr(go_data, 'm_Name', ''))
                print("  " * indent + f"- {gname}")
                for comp in go_data.m_Components:
                    cdata = comp.read()
                    if hasattr(cdata, 'm_Children'):
                        for child_ref in cdata.m_Children:
                            child_tr = child_ref.read()
                            child_go = child_tr.m_GameObject.read()
                            print_tree(child_go, indent + 1, max_depth)
            print_tree(data)
            break
