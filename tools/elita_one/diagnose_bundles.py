import UnityPy
import struct

print("=== Checking Elita grafted mesh in Unity AssetBundle ===")
env_u = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env_u.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        print(f"\nMesh: {name}")
        bp = tree.get('m_BindPose', [])
        print(f"  Bindposes count: {len(bp)}")
        bones_hashes = tree.get('m_BoneNameHashes', [])
        print(f"  Bone name hashes count: {len(bones_hashes)}")
        vdata = bytearray(tree['m_VertexData']['m_DataSize'])
        v_count = tree['m_VertexData']['m_VertexCount']
        print(f"  Vertex count: {v_count}")
        xs, ys, zs = [], [], []
        for i in range(min(v_count, 1000)):
            px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
            xs.append(px); ys.append(py); zs.append(pz)
        print(f"  Stream 0 Pos range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")

print("\n=== Checking Arcee base bundle ===")
env_a = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env_a.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        if name in ['cha_arcee_gs_deluxe2014_00', 'cha_arcee_gs_deluxe2014_01']:
            print(f"\nMesh: {name}")
            bp = tree.get('m_BindPose', [])
            print(f"  Bindposes count: {len(bp)}")
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            v_count = tree['m_VertexData']['m_VertexCount']
            xs, ys, zs = [], [], []
            for i in range(min(v_count, 1000)):
                px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
                xs.append(px); ys.append(py); zs.append(pz)
            print(f"  Stream 0 Pos range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
