import UnityPy
import struct

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            vdata = tree.get('m_VertexData', {})
            v_count = vdata.get('m_VertexCount')
            raw = bytearray(vdata.get('m_DataSize', []))
            s2_offset = 60 * v_count
            print(f"Vehicle Mesh verts: {v_count}, raw len={len(raw)}, s2_offset={s2_offset}")
            bone_usage = {}
            for i in range(v_count):
                off = s2_offset + i * 4
                b0 = struct.unpack_from('<i', raw, off)[0]
                bone_usage[b0] = bone_usage.get(b0, 0) + 1
            print("Bone usage in Arcee vehicle mesh:")
            for b in sorted(bone_usage):
                print(f"  Bone {b}: {bone_usage[b]} verts")
            break
