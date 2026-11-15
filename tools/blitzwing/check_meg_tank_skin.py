import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
from collections import Counter

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

for o in env.objects:
    if o.path_id == 8396146535644667895:
        m = o.read_typetree()
        vd = m["m_VertexData"]
        vc = vd["m_VertexCount"]
        data = bytearray(vd["m_DataSize"])
        # In Megatron:
        # stream 0: 40 bytes
        # stream 1: 16 bytes (UV0, UV1)
        # stream 2: 1 byte bone index? Or 4 bytes?
        # Let's inspect channels
        for c in vd["m_Channels"]:
            print(f"ch: s={c['stream']} off={c['offset']} fmt={c['format']} dim={c['dimension']}")
        s0_size = vc * 40
        s1_size = vc * 16
        s2_offset = s0_size + s1_size
        rem = len(data) - s2_offset
        stride2 = rem // vc
        print(f"Megatron Tank Stride 2: {stride2}")
        b_counts = Counter()
        for i in range(vc):
            b = data[s2_offset + i * stride2]
            b_counts[b] += 1
        print("Megatron Tank bone vertex counts:")
        for b, count in sorted(b_counts.items()):
            print(f"  Bone {b:2d}: {count} vertices")
