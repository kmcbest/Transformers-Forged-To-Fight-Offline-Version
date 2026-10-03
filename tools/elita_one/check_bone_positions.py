import UnityPy
import struct

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_elita_one_grafted':
            vdata = tree.get('m_VertexData', {})
            v_count = vdata.get('m_VertexCount')
            raw = bytearray(vdata.get('m_DataSize', []))
            s2_offset = 44 * v_count
            
            # Check samples of different bones
            bone_samples = {}
            for i in range(v_count):
                off = s2_offset + i * 32
                b0 = struct.unpack_from('<i', raw, off + 16)[0]
                px, py, pz = struct.unpack_from('<3f', raw, i * 40)
                if b0 not in bone_samples:
                    bone_samples[b0] = []
                if len(bone_samples[b0]) < 3:
                    bone_samples[b0].append((px, py, pz))
            
            print(f"Total bones used: {len(bone_samples)}")
            for b in sorted(bone_samples):
                print(f"Bone {b}: sample pos {bone_samples[b][0]}")
            break
