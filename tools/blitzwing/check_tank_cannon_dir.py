import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
import struct

MESH_BUNDLE = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env = UnityPy.load(MESH_BUNDLE)

for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if m["m_Name"] == "cha_blitzwing_gs_01_tank":
            vd = m["m_VertexData"]
            vc = vd["m_VertexCount"]
            data = bytearray(vd["m_DataSize"])
            # Let's find vertices with highest height (top of cannon/turret)
            high_verts = []
            for i in range(vc):
                x, y, z = struct.unpack_from("<fff", data, i * 40)
                if z > 2.0:
                    high_verts.append((x, y, z))
            print(f"Tank highest verts (z > 2.0): count={len(high_verts)}")
            ys = [v[1] for v in high_verts]
            print(f"  y range of highest verts: min={min(ys):.3f}, max={max(ys):.3f}")

            # Let's check extreme y (front vs back)
            min_y_verts = [struct.unpack_from("<fff", data, i * 40) for i in range(vc) if struct.unpack_from("<fff", data, i * 40)[1] < -5.0]
            max_y_verts = [struct.unpack_from("<fff", data, i * 40) for i in range(vc) if struct.unpack_from("<fff", data, i * 40)[1] > 3.8]
            print(f"  verts with y < -5.0 (count={len(min_y_verts)}): z range=[{min(v[2] for v in min_y_verts):.3f}, {max(v[2] for v in min_y_verts):.3f}], x range=[{min(v[0] for v in min_y_verts):.3f}, {max(v[0] for v in min_y_verts):.3f}]")
            print(f"  verts with y > 3.8 (count={len(max_y_verts)}): z range=[{min(v[2] for v in max_y_verts):.3f}, {max(v[2] for v in max_y_verts):.3f}], x range=[{min(v[0] for v in max_y_verts):.3f}, {max(v[0] for v in max_y_verts):.3f}]")
