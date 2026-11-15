import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import UnityPy

MESH_BUNDLE = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(MESH_BUNDLE))

bw_meshes = {}
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        bw_meshes[tt["m_Name"]] = tt

print("Found meshes:", list(bw_meshes.keys()))

# 1. Transform Tank Vertices
src_t = bw_meshes["cha_blitzwing_gs_01_tank"]
vd = src_t["m_VertexData"]
vcount = vd["m_VertexCount"]
data = bytearray(vd["m_DataSize"])
stride0 = 40

xs, ys, zs = [], [], []
for i in range(vcount):
    off = i * stride0
    x, y, z = struct.unpack_from("<fff", data, off)
    nx, ny, nz = struct.unpack_from("<fff", data, off + 12)
    tx, ty, tz, tw = struct.unpack_from("<ffff", data, off + 24)

    # Apply (x, z - 1.549, -y)
    new_x = x
    new_y = z - 1.549
    new_z = -y

    new_nx = nx
    new_ny = nz
    new_nz = -ny

    new_tx = tx
    new_ty = tz
    new_tz = -ty
    new_tw = tw

    struct.pack_into("<fff", data, off, new_x, new_y, new_z)
    struct.pack_into("<fff", data, off + 12, new_nx, new_ny, new_nz)
    struct.pack_into("<ffff", data, off + 24, new_tx, new_ty, new_tz, new_tw)

    xs.append(new_x); ys.append(new_y); zs.append(new_z)

print(f"Transformed Tank: verts={vcount}")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}]")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}]")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}]")

# 2. Transform Jet Vertices & fix UVs
src_j = bw_meshes["cha_blitzwing_gs_02_jet"]
vd_j = src_j["m_VertexData"]
vcount_j = vd_j["m_VertexCount"]
data_j = bytearray(vd_j["m_DataSize"])

j_xs, j_ys, j_zs = [], [], []
for i in range(vcount_j):
    off = i * stride0
    x, y, z = struct.unpack_from("<fff", data_j, off)
    nx, ny, nz = struct.unpack_from("<fff", data_j, off + 12)
    tx, ty, tz, tw = struct.unpack_from("<ffff", data_j, off + 24)

    new_x = x
    new_y = z + 0.30
    new_z = -y

    new_nx = nx
    new_ny = nz
    new_nz = -ny

    new_tx = tx
    new_ty = tz
    new_tz = -ty
    new_tw = tw

    struct.pack_into("<fff", data_j, off, new_x, new_y, new_z)
    struct.pack_into("<fff", data_j, off + 12, new_nx, new_ny, new_nz)
    struct.pack_into("<ffff", data_j, off + 24, new_tx, new_ty, new_tz, new_tw)

    j_xs.append(new_x); j_ys.append(new_y); j_zs.append(new_z)

# Fix UVs in stream 1
stream1_off = vcount_j * 40
fixed_uvs = 0
for i in range(vcount_j):
    off = stream1_off + i * 8
    u, v = struct.unpack_from("<ff", data_j, off)
    if v < 0:
        v += 0.5
        struct.pack_into("<ff", data_j, off, u, v)
        fixed_uvs += 1

# Set bone weights in stream 2 (format 10) to bone 1 (COG)
# In Unity Format 10: 4 uint8 indices
stream2_off = vcount_j * 48
for i in range(vcount_j):
    off = stream2_off + i * 4
    # bone index 1 (COG)
    data_j[off] = 1
    data_j[off+1] = 0
    data_j[off+2] = 0
    data_j[off+3] = 0

print(f"\nTransformed Jet: verts={vcount_j}, fixed {fixed_uvs} UVs, set skinning to COG (bone 1)")
print(f"  X: [{min(j_xs):.3f}, {max(j_xs):.3f}]")
print(f"  Y: [{min(j_ys):.3f}, {max(j_ys):.3f}]")
print(f"  Z: [{min(j_zs):.3f}, {max(j_zs):.3f}]")
