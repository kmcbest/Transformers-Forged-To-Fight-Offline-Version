import UnityPy
import struct

# Check Arcee vehicle mesh front vs back
env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            vdata = tree.get('m_VertexData', {})
            v_count = vdata.get('m_VertexCount')
            raw = bytearray(vdata.get('m_DataSize', []))
            # Bone 0 is chop1_cartail_center_hidden (tail = back of car!)
            # Bone 6 is chop1_cannon_center_hidden or Bone 15 is chop2_head_center (head = front of car!)
            s2_offset = 60 * v_count
            zs_tail = []
            zs_head = []
            for i in range(v_count):
                b0 = struct.unpack_from('<i', raw, s2_offset + i * 4)[0]
                pz = struct.unpack_from('<3f', raw, i * 40)[2]
                if b0 == 0: # cartail
                    zs_tail.append(pz)
                elif b0 == 15: # head
                    zs_head.append(pz)
            print(f"Arcee Vehicle Tail Z: min={min(zs_tail):.2f}, max={max(zs_tail):.2f}, avg={sum(zs_tail)/len(zs_tail):.2f}")
            print(f"Arcee Vehicle Head Z: min={min(zs_head):.2f}, max={max(zs_head):.2f}, avg={sum(zs_head)/len(zs_head):.2f}")
            break
