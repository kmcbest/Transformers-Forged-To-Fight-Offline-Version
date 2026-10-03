import UnityPy

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_elita_one_grafted':
            vdata = tree.get('m_VertexData', {})
            channels = vdata.get('m_Channels', [])
            print("Channels:")
            for i, ch in enumerate(channels):
                print(f"  Ch {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
            break
