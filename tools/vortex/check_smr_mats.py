import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        data = obj.read_typetree()
        mesh_ref = data.get("m_Mesh")
        m_name = ""
        if mesh_ref and mesh_ref["m_PathID"] != 0:
            m_obj = obj.assets_file.objects.get(mesh_ref["m_PathID"])
            if m_obj: m_name = m_obj.read_typetree().get("m_Name", "")
        if "00" in m_name or "01" in m_name:
            mats = []
            for mat_ref in data.get("m_Materials", []):
                mat_obj = obj.assets_file.objects.get(mat_ref["m_PathID"])
                if mat_obj:
                    mats.append(mat_obj.read_typetree().get("m_Name", ""))
            print(f"SMR {m_name} materials: {mats}")
