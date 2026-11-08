import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import struct
import numpy as np

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            vdata = tree.get("m_VertexData", {})
            num_v = vdata.get("m_VertexCount")
            raw = bytes(vdata.get("_typelessdata", []))
            streams = vdata.get("m_Streams", [])
            stride = streams[0].get("stride")
            offset = streams[0].get("offset")
            
            verts = []
            for i in range(num_v):
                pos = offset + i * stride
                x, y, z = struct.unpack_from("<3f", raw, pos)
                verts.append((x, y, z))
            verts = np.array(verts)
            print(f"=== Grindor Vehicle Mesh (cha_grindor_cin_rotf_01) ===")
            print(f"Total Verts: {len(verts)}")
            print(f"X (min, max): [{verts[:, 0].min():.2f}, {verts[:, 0].max():.2f}]")
            print(f"Y (min, max): [{verts[:, 1].min():.2f}, {verts[:, 1].max():.2f}]")
            print(f"Z (min, max): [{verts[:, 2].min():.2f}, {verts[:, 2].max():.2f}]")
            
            # Find extreme vertices
            p_nose = verts[np.argmax(verts[:, 2])]
            p_tail = verts[np.argmin(verts[:, 2])]
            p_top = verts[np.argmax(verts[:, 1])]
            p_bottom = verts[np.argmin(verts[:, 1])]
            p_left = verts[np.argmin(verts[:, 0])]
            p_right = verts[np.argmax(verts[:, 0])]
            
            print(f"Max Z (Nose?): {p_nose}")
            print(f"Min Z (Tail?): {p_tail}")
            print(f"Max Y (Rotor Top?): {p_top}")
            print(f"Min Y (Belly/Wheels?): {p_bottom}")
            print(f"Min X (Left?): {p_left}")
            print(f"Max X (Right?): {p_right}")
            break
