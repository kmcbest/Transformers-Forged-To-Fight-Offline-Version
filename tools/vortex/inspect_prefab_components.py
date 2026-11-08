import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        if data.get("m_Name") == "Grindor_Cin_ROTF":
            print("Found Grindor_Cin_ROTF prefab!")
            for comp in data.get("m_Component", []):
                c_obj = obj.assets_file.objects[comp["component"]["m_PathID"]]
                print(f"  Component: {c_obj.type.name}")
    elif obj.type.name == "SkinnedMeshRenderer":
        data = obj.read_typetree()
        mesh_ref = data.get("m_Mesh")
        m_name = ""
        if mesh_ref and mesh_ref["m_PathID"] != 0:
            m_obj = obj.assets_file.objects[mesh_ref["m_PathID"]]
            m_name = m_obj.read_typetree().get("m_Name", "")
        print(f"SMR: mesh={m_name}, bones={len(data.get('m_Bones', []))}")
