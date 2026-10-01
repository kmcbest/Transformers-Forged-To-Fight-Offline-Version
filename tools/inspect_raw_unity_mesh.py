import UnityPy
import struct
from pathlib import Path

bundle_path = Path("toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        name = tree.get("m_Name")
        vdata = tree.get('m_VertexData', {})
        v_count = vdata.get('m_VertexCount', 0)
        raw_data = bytearray(vdata.get('m_DataSize', []))
        stride = 40
        print(f"Mesh: {name}, v_count: {v_count}")
        xs, ys, zs = [], [], []
        for i in range(v_count):
            px, py, pz = struct.unpack_from('<3f', raw_data, i * stride)
            xs.append(px); ys.append(py); zs.append(pz)
        print(f"  raw px range: [{min(xs):.2f}, {max(xs):.2f}]")
        print(f"  raw py range: [{min(ys):.2f}, {max(ys):.2f}]")
        print(f"  raw pz range: [{min(zs):.2f}, {max(zs):.2f}]")
