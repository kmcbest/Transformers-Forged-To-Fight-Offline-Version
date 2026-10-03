import UnityPy

env = UnityPy.load('assets_redeco/elita_one_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
            hashes = tree.get('m_BoneNameHashes', [])
            bp = tree.get('m_BindPose', [])
            print(f"Redeco cha_arcee_gs_deluxe2014_00:")
            print(f"  m_BindPose count: {len(bp)}")
            print(f"  m_BoneNameHashes count: {len(hashes)}")
            break
