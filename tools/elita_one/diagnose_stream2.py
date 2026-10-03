import UnityPy
import struct

env = UnityPy.load('assets_redeco/elita_one_gs.assetbundle')

# 1. Find Mesh cha_arcee_gs_deluxe2014_00
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
            print("--- cha_arcee_gs_deluxe2014_00 ---")
            print("Vertex count:", tree['m_VertexData']['m_VertexCount'])
            print("Bindposes count:", len(tree.get('m_BindPose', [])))
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            # Check Stream 0 first vertex position
            p0 = struct.unpack_from('<3f', vdata, 0)
            print("First vert pos (Stream 0):", p0)
            # Find Stream 2 offset
            # Let's inspect channels
            channels = tree['m_VertexData']['m_Channels']
            for i, ch in enumerate(channels):
                if ch['dimension'] > 0:
                    print(f"  Channel {i}: stream={ch['stream']}, offset={ch['offset']}, dim={ch['dimension']}, format={ch['format']}")
            
            # Check Stream 2 first vertex bone indices & weights
            # Stream 0 size: 40 * v_count
            # Stream 1 size: UV
            # Let's find stream 2 offset
            s0_size = 40 * tree['m_VertexData']['m_VertexCount']
            # UV stream (Stream 1)
            ch_uv = channels[4]
            # format 1 (half float) * 2 = 4 bytes per vertex
            s1_size = 4 * tree['m_VertexData']['m_VertexCount']
            s2_offset = s0_size + s1_size
            w0 = struct.unpack_from('<4f', vdata, s2_offset)
            idx0 = struct.unpack_from('<4i', vdata, s2_offset + 16)
            print(f"First vert Stream 2: weights={w0}, bone_indices={idx0}")

            # Check bone index range across all vertices
            v_count = tree['m_VertexData']['m_VertexCount']
            max_bone_idx = -1
            min_bone_idx = 999
            for v in range(v_count):
                idx = struct.unpack_from('<4i', vdata, s2_offset + v * 32 + 16)
                for b_i in idx:
                    if b_i > max_bone_idx: max_bone_idx = b_i
                    if b_i < min_bone_idx: min_bone_idx = b_i
            print(f"Bone index range in mesh: [{min_bone_idx}, {max_bone_idx}]")

        elif tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            print("\n--- cha_arcee_gs_deluxe2014_01 ---")
            print("Vertex count:", tree['m_VertexData']['m_VertexCount'])
            print("Bindposes count:", len(tree.get('m_BindPose', [])))
            vdata = bytearray(tree['m_VertexData']['m_DataSize'])
            p0 = struct.unpack_from('<3f', vdata, 0)
            print("First vert pos (Stream 0):", p0)
