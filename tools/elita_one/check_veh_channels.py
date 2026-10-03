import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            vdata = tree.get('m_VertexData', {})
            channels = vdata.get('m_Channels', [])
            print(f"Total size: {len(vdata.get('m_DataSize', []))}, count={vdata.get('m_VertexCount')}")
            for i, ch in enumerate(channels):
                if ch.get('dimension') > 0:
                    print(f"  Ch {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
            skin = tree.get('m_Skin', [])
            print(f"m_Skin length: {len(skin)}")
            if skin:
                print("First 3 skin:", skin[:3])
            break
