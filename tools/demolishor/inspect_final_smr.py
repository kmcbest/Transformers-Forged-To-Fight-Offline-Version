import UnityPy

env = UnityPy.load('assets_redeco/demolishor_gs.assetbundle')

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read_typetree()
        if smr.get("m_Mesh", {}).get("m_PathID") == 243592621990493584:
            print(f"SMR PathID: {obj.path_id}")
            print(f"  m_Mesh: {smr.get('m_Mesh')}")
            print(f"  m_RootBone: {smr.get('m_RootBone')}")
            print(f"  m_Bones count: {len(smr.get('m_Bones', []))}")
            print(f"  m_AABB: {smr.get('m_AABB')}")
            print(f"  First 5 bones: {smr.get('m_Bones')[:5]}")
