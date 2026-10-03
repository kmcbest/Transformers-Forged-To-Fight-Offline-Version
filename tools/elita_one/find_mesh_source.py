import UnityPy
import numpy as np

# Check cha_arcee_gs_deluxe2014_01
env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            print("Found cha_arcee_gs_deluxe2014_01 in Arcee bundle")
        elif tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
            print("Found cha_arcee_gs_deluxe2014_00 in Arcee bundle")

# Let's inspect Elita's grafted mesh in elita_one_mesh.assetbundle
env_elita = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env_elita.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        print(f"Elita bundle mesh: {tree.get('m_Name')}, verts: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
