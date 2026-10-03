import UnityPy
import struct

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
            print("Arcee Robot Mesh:")
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            v_count = tree['m_VertexData']['m_VertexCount']
            xs, ys, zs = [], [], []
            for i in range(min(v_count, 1000)):
                px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
                xs.append(px); ys.append(py); zs.append(pz)
            print(f"  Range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
        elif tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            print("Arcee Vehicle Mesh:")
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            v_count = tree['m_VertexData']['m_VertexCount']
            xs, ys, zs = [], [], []
            for i in range(min(v_count, 1000)):
                px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
                xs.append(px); ys.append(py); zs.append(pz)
            print(f"  Range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
