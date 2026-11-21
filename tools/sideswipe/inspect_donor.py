import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

donor_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle"
donor_env = UnityPy.load(donor_path)

for obj in donor_env.objects:
    if obj.type.name in ["MeshRenderer", "ParticleSystemRenderer", "TrailRenderer"]:
        data = obj.read()
        go_name = data.m_GameObject.read().m_Name
        print(f"Renderer {obj.type.name} on GO: {go_name}")
