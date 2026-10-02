import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

print("Materials in arcee bundle:")
for obj in env.objects:
    if obj.type.name == "Material":
        mat = obj.read()
        print(f"  Material: {mat.m_Name}")
        # print shader name and texture properties
        # print(mat.to_dict())

print("\nSkinnedMeshRenderers and Meshes in arcee bundle:")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        print(f"  SMR: {smr.m_GameObject.read().m_Name}")
    elif obj.type.name == "Mesh":
        mesh = obj.read()
        verts_count = len(mesh.m_Vertices) if hasattr(mesh, 'm_Vertices') and mesh.m_Vertices else (mesh.m_VertexData.m_VertexCount if hasattr(mesh, 'm_VertexData') else 0)
        print(f"  Mesh: {mesh.m_Name}, submeshes: {len(mesh.m_SubMeshes)}, verts: {verts_count}")
