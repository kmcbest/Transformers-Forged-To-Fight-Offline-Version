import UnityPy
import struct

def inspect_stream2(bundle_path, mesh_name):
    print(f"\n--- {bundle_path} : {mesh_name} ---")
    env = UnityPy.load(bundle_path)
    for obj in env.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            if tree.get('m_Name') == mesh_name:
                vdata = tree.get('m_VertexData', {})
                v_count = vdata.get('m_VertexCount')
                raw = bytearray(vdata.get('m_DataSize', []))
                s2_offset = 44 * v_count
                print(f"v_count={v_count}, raw len={len(raw)}, expected={76 * v_count}")
                for i in range(5):
                    off = s2_offset + i * 32
                    w0, w1, w2, w3 = struct.unpack_from('<4f', raw, off)
                    b0, b1, b2, b3 = struct.unpack_from('<4i', raw, off + 16)
                    print(f"  v{i}: bones=[{b0}, {b1}, {b2}, {b3}], weights=[{w0:.2f}, {w1:.2f}, {w2:.2f}, {w3:.2f}]")

inspect_stream2('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle', 'cha_arcee_gs_deluxe2014_00')
inspect_stream2('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle', 'cha_elita_one_grafted')
inspect_stream2('assets_redeco/elita_one_gs.assetbundle', 'cha_arcee_gs_deluxe2014_00')
