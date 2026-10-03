import UnityPy

c_env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
i_env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')

v_tree = None
for obj in c_env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_elita_one_vehicle_grafted':
        v_tree = obj.read_typetree()
        break

a_tree = None
for obj in i_env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
        a_tree = obj.read_typetree()
        break

print("Vehicle mesh extracted:", v_tree is not None)
print("Arcee 01 mesh extracted:", a_tree is not None)

print("V submeshes:", len(v_tree['m_SubMeshes']))
print("A submeshes:", len(a_tree['m_SubMeshes']))
print("V bindposes:", len(v_tree['m_BindPose']))
print("A bindposes:", len(a_tree['m_BindPose']))
print("V bones name/hash:", v_tree.get('m_BoneNameHashes', []))
print("A bones name/hash:", a_tree.get('m_BoneNameHashes', []))
