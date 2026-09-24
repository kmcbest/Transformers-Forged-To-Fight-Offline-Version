# -*- coding: utf-8 -*-
import sys
import UnityPy
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            vdata = tree.get('m_VertexData', {})
            channels = vdata.get('m_Channels', [])
            print("m_VertexCount:", vdata.get('m_VertexCount'))
            print("Data size:", len(vdata.get('m_DataSize', b'')))
            print("Channels count:", len(channels))
            for i, ch in enumerate(channels):
                if ch.get('dimension') > 0:
                    print(f"  Channel {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dimension={ch.get('dimension')}")
            break
