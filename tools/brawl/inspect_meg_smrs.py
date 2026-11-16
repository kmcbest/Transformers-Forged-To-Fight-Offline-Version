import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go_name = smr.m_GameObject.read().m_Name if smr.m_GameObject else "None"
        mesh_name = smr.m_Mesh.read().m_Name if smr.m_Mesh else "None"
        print(f"SMR on {go_name}, Mesh: {mesh_name}, Bones count: {len(smr.m_Bones)}")
        if "01" in mesh_name:
            for idx, b in enumerate(smr.m_Bones):
                tr = b.read()
                b_name = tr.m_GameObject.read().m_Name if tr and tr.m_GameObject else "None"
                print(f"  [{idx:2d}] {b_name}")
