import UnityPy
import struct

c_env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in c_env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        print(f"Mesh: {tree['m_Name']}")
        vdata = bytearray(tree['m_VertexData']['m_DataSize'])
        p0 = struct.unpack_from('<3f', vdata, 0)
        print(f"  First vert: {p0}")
        # Find min/max X, Y, Z
        v_count = tree['m_VertexData']['m_VertexCount']
        xs, ys, zs = [], [], []
        for i in range(min(v_count, 1000)):
            px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
            xs.append(px); ys.append(py); zs.append(pz)
        print(f"  Sample range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
