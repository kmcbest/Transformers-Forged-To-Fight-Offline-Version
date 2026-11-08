import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read_typetree()
        m_name = data.get("m_Name", "")
        tex_envs = data.get("m_SavedProperties", {}).get("m_TexEnvs", {})
        print(f"Material: {m_name}")
        if isinstance(tex_envs, dict):
            for k, v in tex_envs.items():
                print(f"   {k}: {v}")
        elif isinstance(tex_envs, list):
            for item in tex_envs:
                print(f"   item: {item}")
