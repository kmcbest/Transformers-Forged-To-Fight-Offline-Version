import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
import struct

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
MESH_BUNDLE = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"

env_d = UnityPy.load(DONOR_BUNDLE)
for o in env_d.objects:
    if o.path_id == 8396146535644667895:
        m = o.read_typetree()
        vd = m["m_VertexData"]
        vc = vd["m_VertexCount"]
        data = bytearray(vd["m_DataSize"])
        xs, ys, zs = [], [], []
        # Megatron format: let's check channel formats
        chans = vd["m_Channels"]
        print(f"Megatron Tank Mesh channels: {len(chans)}")
        for i, c in enumerate(chans):
            print(f"  ch {i}: stream={c['stream']} offset={c['offset']} fmt={c['format']} dim={c['dimension']}")
        # stream 0: pos (dim 3, fmt 0 = float32), normal (dim 3, fmt 0), tangent (dim 4, fmt 0) -> 40 bytes
        for i in range(vc):
            off = i * 40
            x, y, z = struct.unpack_from("<fff", data, off)
            xs.append(x); ys.append(y); zs.append(z)
        print(f"Megatron Tank raw verts ({vc}): X=[{min(xs):.3f}, {max(xs):.3f}] Y=[{min(ys):.3f}, {max(ys):.3f}] Z=[{min(zs):.3f}, {max(zs):.3f}]")

env_m = UnityPy.load(MESH_BUNDLE)
for o in env_m.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if "tank" in m["m_Name"].lower() or "01" in m["m_Name"].lower():
            vd = m["m_VertexData"]
            vc = vd["m_VertexCount"]
            data = bytearray(vd["m_DataSize"])
            xs, ys, zs = [], [], []
            for i in range(vc):
                off = i * 40
                x, y, z = struct.unpack_from("<fff", data, off)
                xs.append(x); ys.append(y); zs.append(z)
            print(f"Blitzwing Tank raw verts '{m['m_Name']}' ({vc}): X=[{min(xs):.3f}, {max(xs):.3f}] Y=[{min(ys):.3f}, {max(ys):.3f}] Z=[{min(zs):.3f}, {max(zs):.3f}]")
        if "jet" in m["m_Name"].lower() or "02" in m["m_Name"].lower():
            vd = m["m_VertexData"]
            vc = vd["m_VertexCount"]
            data = bytearray(vd["m_DataSize"])
            xs, ys, zs = [], [], []
            for i in range(vc):
                off = i * 40
                x, y, z = struct.unpack_from("<fff", data, off)
                xs.append(x); ys.append(y); zs.append(z)
            print(f"Blitzwing Jet raw verts '{m['m_Name']}' ({vc}): X=[{min(xs):.3f}, {max(xs):.3f}] Y=[{min(ys):.3f}, {max(ys):.3f}] Z=[{min(zs):.3f}, {max(zs):.3f}]")
