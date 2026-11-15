import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
from collections import Counter

MESH_BUNDLE = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env = UnityPy.load(MESH_BUNDLE)

for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if m["m_Name"] == "cha_blitzwing_gs_01_tank":
            vd = m["m_VertexData"]
            vc = vd["m_VertexCount"]
            data = bytearray(vd["m_DataSize"])
            # stream 0: 40 bytes/vert, stream 1: 8 bytes/vert, stream 2: 4 bytes (or 1 byte?)
            # Wait, let's check channel 13 stream offset
            # ch 0: s=0, off=0 (40 bytes)
            # ch 4: s=1, off=0 (8 bytes)
            # ch 13: s=2, off=0, fmt=10 (UInt8), dim=1
            s0_size = vc * 40
            s1_size = vc * 8
            s2_offset = s0_size + s1_size
            # fmt=10 with dim=1 is 1 byte, but Unity pads streams to 4 bytes or 1 byte?
            # Let's inspect total data size
            total_size = len(data)
            print(f"Total data size: {total_size}, s0={s0_size}, s1={s1_size}, rem={total_size - s0_size - s1_size}")
            rem = total_size - s0_size - s1_size
            stride2 = rem // vc
            print(f"Stride 2: {stride2}")
            bone_indices = []
            for i in range(vc):
                b = data[s2_offset + i * stride2]
                bone_indices.append(b)
            print("Bone index counts in Tank:", Counter(bone_indices))
        if m["m_Name"] == "cha_blitzwing_gs_02_jet":
            vd = m["m_VertexData"]
            vc = vd["m_VertexCount"]
            data = bytearray(vd["m_DataSize"])
            s0_size = vc * 40
            s1_size = vc * 8
            s2_offset = s0_size + s1_size
            total_size = len(data)
            rem = total_size - s0_size - s1_size
            stride2 = rem // vc
            bone_indices = []
            for i in range(vc):
                b = data[s2_offset + i * stride2]
                bone_indices.append(b)
            print("Bone index counts in Jet:", Counter(bone_indices))
