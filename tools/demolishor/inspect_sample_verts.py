# -*- coding: utf-8 -*-
import sys
import struct
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            vdata = tree.get('m_VertexData', {})
            raw_bytes = bytes(vdata.get('m_DataSize', []))
            print("Total raw bytes:", len(raw_bytes))
            # First 5 positions in stream 0 (stride 40 bytes)
            for i in range(5):
                pos = struct.unpack_from('<3f', raw_bytes, i * 40)
                norm = struct.unpack_from('<3f', raw_bytes, i * 40 + 12)
                print(f"Vertex {i}: pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}) norm=({norm[0]:.3f}, {norm[1]:.3f}, {norm[2]:.3f})")
            break
