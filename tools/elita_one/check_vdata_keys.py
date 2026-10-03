import UnityPy

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_elita_one_grafted':
            vdata = tree.get('m_VertexData', {})
            for k in vdata:
                if k != 'm_DataSize':
                    print(f"{k}: {vdata[k]}")
            break
