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
            channels = vdata.get('m_Channels', [])
            for i, ch in enumerate(channels):
                if ch.get('dimension') > 0:
                    print(f"Channel {i}: stream={ch['stream']}, offset={ch['offset']}, format={ch['format']}, dim={ch['dimension']}")
            
            # Print m_Skin or m_VariableBoneCountWeights
            print("m_Skin len:", len(tree.get('m_Skin', [])))
            skin = tree.get('m_Skin', [])
            if skin:
                print("First 3 skin entries:", skin[:3])
            
            vb = tree.get('m_VariableBoneCountWeights', {})
            print("m_VariableBoneCountWeights keys:", list(vb.keys()) if vb else "None")
            break
