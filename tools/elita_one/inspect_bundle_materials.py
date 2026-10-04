import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle"
env = UnityPy.load(bundle_path)

print("=== MATERIALS IN BUNDLE ===")
for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        tt = obj.read_typetree()
        print(f"\nMaterial: {data.m_Name} (PathID: {obj.path_id})")
        print(f"  Shader: {tt.get('m_Shader', {}).get('m_PathID')}")
        # Textures
        tex_envs = tt.get('m_SavedProperties', {}).get('m_TexEnvs', [])
        for k, v in tex_envs:
            tex_id = v.get('m_Texture', {}).get('m_PathID')
            print(f"    TexEnv '{k}': PathID={tex_id}")
        # Floats
        floats = dict(tt.get('m_SavedProperties', {}).get('m_Floats', []))
        print(f"    _Mode={floats.get('_Mode')}, _emissive_range={floats.get('_emissive_range')}, _emissive_overbright_range={floats.get('_emissive_overbright_range')}")
        colors = dict(tt.get('m_SavedProperties', {}).get('m_Colors', []))
        print(f"    _emissive_intensity_col={colors.get('_emissive_intensity_col')}")

print("\n=== SKINNED MESH RENDERERS IN BUNDLE ===")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        game_obj = tt.get('m_GameObject', {}).get('m_PathID')
        mesh_id = tt.get('m_Mesh', {}).get('m_PathID')
        mats = [m.get('m_PathID') for m in tt.get('m_Materials', [])]
        print(f"SMR (PathID: {obj.path_id}): GameObject PathID={game_obj}, Mesh PathID={mesh_id}, Materials={mats}")

print("\n=== TEXTURES IN BUNDLE ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        print(f"Texture2D: {data.m_Name} (PathID: {obj.path_id}), size=({data.m_Width}x{data.m_Height}), format={data.m_TextureFormat}")
