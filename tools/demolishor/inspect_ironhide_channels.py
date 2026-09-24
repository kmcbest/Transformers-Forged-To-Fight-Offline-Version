import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_ironhide_cin_rotf_00':
        m = obj.read()
        print("Ironhide Mesh properties:")
        print("  Vertices:", len(m.m_Vertices) if m.m_Vertices else "None")
        print("  Skin count:", len(m.m_Skin) if m.m_Skin else "None")
        
        # Check typetree
        tree = obj.read_typetree()
        v_data = tree.get('m_VertexData', {})
        print("  VertexCount:", v_data.get('m_VertexCount'))
        print("  Channels:", len(v_data.get('m_Channels', [])))
        for ch_idx, ch in enumerate(v_data.get('m_Channels', [])):
            print(f"    Channel {ch_idx}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dimension={ch.get('dimension')}")
        break
