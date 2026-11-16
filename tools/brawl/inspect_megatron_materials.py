import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

print("--- MATERIALS IN MEGATRON ROTF BUNDLE ---")
for obj in env.objects:
    if obj.type.name == "Material":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        print(f"Material: {name} (PID={obj.path_id})")
        tex_envs = tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        for tex_name, tex_prop in tex_envs:
            tex_pid = tex_prop.get("m_Texture", {}).get("m_PathID")
            if tex_pid != 0:
                print(f"    {tex_name} -> PID={tex_pid}")

print("\n--- TEXTURES IN MEGATRON ROTF BUNDLE ---")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tt = obj.read_typetree()
        print(f"Texture2D: {tt.get('m_Name')} (PID={obj.path_id})")
