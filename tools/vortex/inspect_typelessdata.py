import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import struct
import numpy as np

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_vortex_vh_grafted":
            vdata = tree.get("m_VertexData", {})
            channels = vdata.get("m_Channels", [])
            print("Channels:")
            for i, ch in enumerate(channels):
                print(f"  Ch {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
            raw = bytes(vdata.get("_typelessdata", []))
            print(f"raw length: {len(raw)}")
            streams = vdata.get("m_Streams", [])
            for s_idx, st in enumerate(streams):
                print(f"  Stream {s_idx}: channelMask={st.get('channelMask')}, offset={st.get('offset')}, stride={st.get('stride')}, dividerOp={st.get('dividerOp')}, frequency={st.get('frequency')}")
            
            num_v = vdata.get("m_VertexCount")
            stride = streams[0].get("stride")
            st_offset = streams[0].get("offset")
            print(f"Reading {num_v} vertices from stream 0 (offset {st_offset}, stride {stride})...")
            
            verts = []
            for i in range(num_v):
                pos = st_offset + i * stride
                x, y, z = struct.unpack_from("<3f", raw, pos)
                verts.append((x, y, z))
            verts = np.array(verts)
            print(f"X range: [{verts[:, 0].min():.2f}, {verts[:, 0].max():.2f}]")
            print(f"Y range: [{verts[:, 1].min():.2f}, {verts[:, 1].max():.2f}]")
            print(f"Z range: [{verts[:, 2].min():.2f}, {verts[:, 2].max():.2f}]")
            
            # Find extreme points
            y_max_pt = verts[np.argmax(verts[:, 1])]
            y_min_pt = verts[np.argmin(verts[:, 1])]
            z_max_pt = verts[np.argmax(verts[:, 2])]
            z_min_pt = verts[np.argmin(verts[:, 2])]
            print(f"Y max point: {y_max_pt}")
            print(f"Y min point: {y_min_pt}")
            print(f"Z max point: {z_max_pt}")
            print(f"Z min point: {z_min_pt}")
            break
