import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

print("=== TEXTURES ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read_typetree()
        print(f"Texture2D PID={o.path_id}: name='{t.get('m_Name')}' {t.get('m_Width')}x{t.get('m_Height')} fmt={t.get('m_TextureFormat')}")

print("\n=== MATERIALS ===")
for o in env.objects:
    if o.type.name == "Material":
        t = o.read_typetree()
        shader_pid = t.get("m_Shader", {}).get("m_PathID")
        tex_envs = [(k, v.get("m_Texture", {}).get("m_PathID")) for k, v in t.get("m_SavedProperties", {}).get("m_TexEnvs", [])]
        print(f"Material PID={o.path_id}: name='{t.get('m_Name')}' shader_pid={shader_pid}")
        for k, tex_id in tex_envs:
            if tex_id != 0:
                print(f"    {k} -> {tex_id}")

print("\n=== MONOBEHAVIOURS ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        if "TextureHip" in t or "TextureFoot" in t:
            print(f"MonoBehaviour PID={o.path_id}: TextureHip={t.get('TextureHip')} TextureFoot={t.get('TextureFoot')}")
