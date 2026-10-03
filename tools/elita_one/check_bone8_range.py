import UnityPy
import struct

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            vdata = tree.get('m_VertexData', {})
            v_count = vdata.get('m_VertexCount')
            raw = bytearray(vdata.get('m_DataSize', []))
            s2_offset = 60 * v_count
            xs, ys, zs = [], [], []
            for i in range(v_count):
                off2 = s2_offset + i * 4
                b0 = struct.unpack_from('<i', raw, off2)[0]
                if b0 == 8:
                    px, py, pz = struct.unpack_from('<3f', raw, i * 40)
                    xs.append(px); ys.append(py); zs.append(pz)
            print(f"Bone 8 vertices in Arcee vehicle mesh ({len(xs)} verts):")
            print(f"  Range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
            break
