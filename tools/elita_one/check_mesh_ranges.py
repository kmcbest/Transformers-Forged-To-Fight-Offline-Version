import UnityPy
import struct
import os

bundle_path = 'assets_redeco/elita_one_gs.assetbundle'
if not os.path.exists(bundle_path):
    bundle_path = 'extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle'

print(f"Loading bundle: {bundle_path}")
env = UnityPy.load(bundle_path)
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        vdata = bytearray(tree['m_VertexData']['m_DataSize'])
        v_count = tree['m_VertexData']['m_VertexCount']
        xs, ys, zs = [], [], []
        for i in range(min(v_count, 1000)):
            px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
            xs.append(px); ys.append(py); zs.append(pz)
        print(f"Mesh: {name}, count={v_count}")
        print(f"  Range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
        print(f"  LocalAABB Center: {tree.get('m_LocalAABB', {}).get('m_Center')}")
        print(f"  LocalAABB Extent: {tree.get('m_LocalAABB', {}).get('m_Extent')}")

# Also check Unity project exported assets if any
unity_asset = 'toolchain/unity_build_project/Assets/AssetBundles/elita_one.assetbundle'
if os.path.exists(unity_asset):
    print(f"\nLoading Unity AssetBundle: {unity_asset}")
    env2 = UnityPy.load(unity_asset)
    for obj in env2.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            name = tree.get('m_Name')
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            v_count = tree['m_VertexData']['m_VertexCount']
            xs, ys, zs = [], [], []
            for i in range(min(v_count, 1000)):
                px, py, pz = struct.unpack_from('<3f', vdata, i * 40)
                xs.append(px); ys.append(py); zs.append(pz)
            print(f"Mesh: {name}, count={v_count}")
            print(f"  Range: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
