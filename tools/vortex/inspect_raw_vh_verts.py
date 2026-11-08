import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_vortex_vh_grafted":
            m = obj.read()
            # print vertex bounds
            verts = getattr(m, 'm_Vertices', getattr(m, 'vertices', None))
            print("m attributes:", [a for a in dir(m) if not a.startswith('__')])
            # Let's inspect raw vertex stream
            vdata = tree.get("m_VertexData", {})
            channels = vdata.get("m_Channels", [])
            data_size = vdata.get("m_DataSize")
            # In UnityPy, vertex stream 0 bytes:
            raw = vdata.get("_typelessdata")
            if raw:
                import struct
                # stream 0: offset 0 is float x, y, z (12 bytes)
                # stride is 40 or whatever
                # let's find stride
                streams = vdata.get("m_Streams", [])
                stride = streams[0].get("stride")
                num_v = vdata.get("m_VertexCount")
                print(f"Num vertices={num_v}, stride={stride}")
                all_x, all_y, all_z = [], [], []
                for i in range(num_v):
                    x, y, z = struct.unpack_from("<3f", raw, i * stride)
                    all_x.append(x)
                    all_y.append(y)
                    all_z.append(z)
                print(f"X: [{min(all_x):.2f}, {max(all_x):.2f}], center={np.mean(all_x):.2f}")
                print(f"Y: [{min(all_y):.2f}, {max(all_y):.2f}], center={np.mean(all_y):.2f}")
                print(f"Z: [{min(all_z):.2f}, {max(all_z):.2f}], center={np.mean(all_z):.2f}")
