import sys
import struct
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

e_env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

def inspect_mesh_vdata(env, mesh_name):
    for obj in env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            if tree.get("m_Name") == mesh_name:
                vdata = tree.get("m_VertexData", {})
                vc = vdata.get("m_VertexCount", 0)
                raw = vdata.get("m_DataSize", b"")
                stride = len(raw) // vc if vc else 0
                channels = vdata.get("m_Channels", [])
                
                # Sample 5 vertices
                xs, ys, zs = [], [], []
                for i in range(vc):
                    x, y, z = struct.unpack_from("<3f", raw, i * stride)
                    xs.append(x); ys.append(y); zs.append(z)
                
                print(f"Mesh '{mesh_name}': {vc} verts, stride: {stride}")
                print(f"  Channels: {len(channels)}")
                for ch in channels:
                    print(f"    stream: {ch.get('stream')}, offset: {ch.get('offset')}, format: {ch.get('format')}, dim: {ch.get('dimension')}")
                print(f"  X range: [{min(xs):.3f}, {max(xs):.3f}]")
                print(f"  Y range: [{min(ys):.3f}, {max(ys):.3f}]")
                print(f"  Z range: [{min(zs):.3f}, {max(zs):.3f}]")
                print(f"  AABB Center: {tree.get('m_LocalAABB', {}).get('m_Center')}")
                print(f"  AABB Extent: {tree.get('m_LocalAABB', {}).get('m_Extent')}")
                return tree

print("=== Arcee Ground Truth Mesh ===")
a_tree = inspect_mesh_vdata(a_env, "cha_arcee_gs_deluxe2014_00")

print("\n=== Elita One Compiled Mesh ===")
e_tree = inspect_mesh_vdata(e_env, "cha_elita_one_gs_00")
